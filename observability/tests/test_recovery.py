from datetime import datetime, timedelta, timezone
import unittest

from observability.recovery import recovery


class RecoveryTests(unittest.TestCase):
    def test_needs_three_consecutive_windows_and_distinguishes_readiness(self):
        origin=datetime(2026,11,18,tzinfo=timezone.utc)
        def at(second):
            return (origin+timedelta(seconds=second)).isoformat()
        events=[{'action':action,'timestamp_utc':at(t),'monotonic_ns':t,'instance_id':'I3','exit_code':0}
                for action,t in zip(('stop','start','ready'),(90,150,160))]
        samples=[]
        for i in range(1800):
            second=i/10
            good=not 90<=second<100
            samples.append({'request_id':str(i),'phase':'measure','started_utc':at(second),'completed_utc':at(second+.05),
                            'status':200 if good else 503,'contract_ok':good,'duration_ms':50})
        result=recovery(samples,events,at(0))
        self.assertEqual(result['before_success_rps'],10)
        self.assertEqual(result['recovery_at'],at(100))
        self.assertEqual(result['seconds_from_stop'],10)
        self.assertIsNone(result['seconds_from_ready'])
        self.assertTrue(result['recovered_before_ready'])
        self.assertIsNone(result['windows'][0]['meets_recovery_slo'])
