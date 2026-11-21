from collections import Counter
import csv
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.schedule import lock_schedule, schedule


class ScheduleTests(unittest.TestCase):
    def test_campaign_counts_and_confirmation_pairs(self):
        plan=schedule()
        self.assertEqual(plan,schedule())
        self.assertEqual(Counter(r['day'] for r in plan['performance']),{9:54,10:41,11:9})
        self.assertEqual(sum(r['keys'] for r in plan['mapping']),60000)
        self.assertTrue(all(r['target_rps'] is None for r in plan['performance']))
        confirm=[r for r in plan['performance'] if r['confirm']]
        self.assertEqual(len(confirm),8)
        self.assertEqual({(r['scenario'],r['algorithm'],r['condition']) for r in confirm},
                         {('B2','rr','H'),('B2','lc','H'),('A3','ch-id','uniform'),('A3','iph','uniform')})
        for block in (1,2,3):
            paired=[[r['algorithm'] for r in plan['performance'] if r['scenario']==scenario
                      and r['condition']=='M' and r['block']==block] for scenario in ('B2','A1','A2')]
            self.assertEqual(paired,[paired[0]]*3)

    def test_rates_are_shared_and_measurement_windows_match_protocol(self):
        data=schedule({'cpu-fixed':20,'mixed-delay':40,'quote':10})['performance']
        self.assertEqual({r['target_rps'] for r in data if r['scenario'] in ('B0','B1','B4') and r['condition']=='M'},{12})
        self.assertEqual({(r['target_rps'],r['measure_seconds']) for r in data if r['scenario']=='A2'},{(24,300)})
        self.assertTrue(all(r['vus']==r['target_rps'] * 6 for r in data))

    def test_locked_schedule_preserves_paired_input_and_hashes(self):
        plan=schedule({'cpu-fixed':2,'mixed-delay':2,'quote':2})
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            hashes=lock_schedule(plan,root,120)
            rows=plan['performance']
            first=lambda scenario: next(row for row in rows if row['scenario']==scenario and row['condition']=='M')
            payload=lambda row: (root/row['trace_path']).read_bytes()
            self.assertEqual(payload(first('B2')),payload(first('A1')))
            self.assertTrue(payload(first('A2')).startswith(payload(first('B2'))))
            default=list(csv.DictReader(payload(first('B1')).decode().splitlines()))
            direct=list(csv.DictReader(payload(first('B4')).decode().splitlines()))
            quote=list(csv.DictReader(payload(first('B3')).decode().splitlines()))
            self.assertEqual(default,[row | {'effective_ip':ip['effective_ip']} for row,ip in zip(direct,default)])
            self.assertTrue(all(not row['effective_ip'] for row in direct))
            self.assertTrue(all(not row['effective_ip'] for row in quote))
            key=plan['mapping'][0]
            self.assertEqual(sha256((root/key['key_path']).read_bytes()).hexdigest(),key['key_sha256'])
            weights=(root/key['weight_path']).read_bytes()
            self.assertEqual(sha256(weights).hexdigest(),key['weight_sha256'])
            self.assertEqual(sum(int(r['weight']) for r in csv.DictReader(weights.decode().splitlines())),180)
            self.assertEqual(sha256(payload(first('B2'))).hexdigest(),hashes[Path(first('B2')['trace_path']).name])

    def test_fast_v4_campaign_keeps_full_matrix_with_short_windows(self):
        plan=schedule({'cpu-fixed':80,'mixed-delay':320,'quote':320},fast_campaign=True)
        self.assertEqual(len(plan['performance']),104)
        self.assertEqual(len(plan['mapping']),60)
        self.assertTrue(all(r['warmup_seconds']==10 and r['cooldown_seconds']==3 for r in plan['performance']))
        self.assertEqual({r['measure_seconds'] for r in plan['performance'] if r['scenario']=='A2'},{55})
        self.assertEqual({r['measure_seconds'] for r in plan['performance'] if r['scenario']!='A2'},{15})
        self.assertTrue(all(r['target_rps']==100 and r['concurrency']==8 and r['keys']==1000 for r in plan['mapping']))
        with TemporaryDirectory() as tmp:
            lock_schedule(plan,Path(tmp),10)
            self.assertTrue((Path(tmp)/'schedule.csv').is_file())
