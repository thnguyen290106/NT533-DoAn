import unittest

from analysis.pilot_gate import evaluate, nginx_timings, select_r_ref, warmup_stability


class PilotGateTests(unittest.TestCase):
    def test_nginx_warmup_keeps_end_to_end_slo_and_success_rate(self):
        anchor='2026-11-20T14:00:00+00:00'
        first='2026-11-20T14:04:01+00:00'
        second='2026-11-20T14:04:31+00:00'
        warm=[{'phase':'warmup','phase_started_utc':anchor,'started_utc':at,'completed_utc':at,
               'request_id':str(i),'status':200,'contract_ok':True,'duration_ms':delay}
              for i,(at,delay) in enumerate([(first,51),(second,91)])]
        server={'0':38,'1':38}
        self.assertFalse(warmup_stability(warm,300)['stable'])
        result=warmup_stability(warm,300,server)
        self.assertTrue(result['stable'])
        self.assertEqual(result['p95_source'],'nginx')
        self.assertEqual(result['windows'][1]['loadgen_ms']['p99'],91)
        self.assertEqual(result['windows'][1]['nginx_ms']['p99'],38)
        self.assertFalse(warmup_stability(warm,300,{'0':38,'1':45})['stable'])
        self.assertFalse(warmup_stability([warm[0],warm[0],warm[1]],300,server)['stable'])
        measurement=[{'phase':'measure','request_id':str(i),'status':200,'contract_ok':True,'duration_ms':500}
                     for i in range(600)]
        observed=evaluate('cpu-fixed',10,measurement,dropped=0,loadgen_ok=True,warmup_stable=result['stable'])
        self.assertTrue(observed['valid'])
        self.assertFalse(observed['slo_passed'])

    def test_nginx_join_excludes_downstream_and_rejects_broken_evidence(self):
        entry={'request_id':'a','route':'/api/orders/quote','peer_ip':'loadgen','status':200,'request_time_s':'0.038'}
        joined=nginx_timings([entry | {'route':'/internal/inventory'},entry],{'a'},'loadgen','/api/orders/quote')
        self.assertEqual(joined,{'a':38})
        for logs in ([entry,entry],[],[entry | {'request_time_s':'nan'}],[entry | {'status':503}]):
            with self.subTest(logs=logs), self.assertRaises(ValueError):
                nginx_timings(logs,{'a'},'loadgen','/api/orders/quote')
    def test_valid_overload_is_distinct_from_bad_client_or_contract(self):
        rows=[{'phase':'measure','request_id':f'{i:032x}','status':200,'contract_ok':True,'duration_ms':10}
              for i in range(600)]
        rows[-6:]=[r | {'status':503,'contract_ok':False} for r in rows[-6:]]
        result=evaluate('cpu-fixed',10,rows,dropped=0,loadgen_ok=True,warmup_stable=True)
        self.assertTrue(result['valid'])
        self.assertFalse(result['slo_passed'])
        self.assertEqual(result['error_ratio'],.01)
        self.assertFalse(evaluate('cpu-fixed',10,rows,dropped=1,loadgen_ok=True,warmup_stable=True)['valid'])
        rows[0]['contract_ok']=False
        self.assertIn('contract',evaluate('cpu-fixed',10,rows,dropped=0,loadgen_ok=True,warmup_stable=True)['invalid_reason'])

    def test_reference_needs_two_failures_and_an_earlier_pass(self):
        def receipt(rate,passed,valid=True):
            return {'profile':'quote','rate':rate,'valid':valid,'slo_passed':passed}
        self.assertIsNone(select_r_ref('quote',[receipt(10,True),receipt(20,False),receipt(20,False,False)]))
        locked=select_r_ref('quote',[receipt(10,True),receipt(20,False),receipt(20,False)])
        self.assertEqual(locked,{'R_ref':20,'H':20,'M':12,'previous_pass_rps':10})
        self.assertIsNone(select_r_ref('quote',[receipt(10,False),receipt(10,False)]))
        self.assertEqual(select_r_ref('quote',[receipt(1,True),receipt(2,True),receipt(5,True),receipt(10,False),receipt(10,False)])['M'],6)
