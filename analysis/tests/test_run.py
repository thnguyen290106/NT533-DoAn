import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from analysis.run import check_trace, digest, execute, preflight, validate_target, workload_plan
from analysis.trace import trace


class RunnerTests(unittest.TestCase):
    def test_trace_boundaries_and_private_target(self):
        scenario, offset, _ = workload_plan({'rate': 5, 'warmup_seconds': 4, 'measure_seconds': 3, 'vus': 30}, 35)
        self.assertEqual(scenario['measure']['startTime'], '4s')
        self.assertEqual(offset, {'warmup': 0, 'measure': 20})
        for bad in ('http://8.8.8.8:8081', 'http://192.168.1.9:8080', 'http://user@192.168.1.9:8081'):
            with self.assertRaises(ValueError):
                validate_target(bad)

    def test_failed_execution_keeps_raw_and_receipt(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.csv'
            source.write_bytes(trace(53301, 'trace', 'quote', 2))
            plan = {'base_url': 'http://192.168.1.2:8081', 'seed': 53301, 'dry_run': True, 'trace_sha256': digest(source)}
            facts = {'commit': '1' * 40, 'config_sha256': '2' * 64, 'protocol_sha256': '3' * 64,
                     'image_digests': {'order': 'sha256:' + '4' * 64}}
            self.assertEqual(check_trace(source), 2)
            with patch('analysis.run.shutil.which', return_value='/test/bin/k6'), patch('analysis.run.subprocess.run') as run:
                def fail(command, stdout, stderr, **options):
                    stdout.write('stdout evidence')
                    stderr.write('stderr evidence')
                    Path(command[-2].split('=', 1)[1]).write_text('raw evidence')
                    return type('Result', (), {'returncode': 99})()
                run.side_effect = fail
                dest = root / 'attempt-a1'
                self.assertEqual(execute(plan, source, facts, dest), 1)
                self.assertEqual(json.loads((dest / 'manifest.json').read_text())['status'], 'invalid')
                self.assertEqual((dest / 'exit-code.txt').read_text(), '99\n')
                self.assertIn('k6-raw.json', (dest / 'SHA256SUMS').read_text())
                with self.assertRaises(FileExistsError):
                    execute(plan, source, facts, dest)

    def test_direct_catalog_only_accepts_a_b4_loopback_trace(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/'trace.csv'
            source.write_bytes(trace(53301,'B4','cpu-fixed',3,actual_ip=True))
            facts={'commit':'1'*40,'config_sha256':'2'*64,'protocol_sha256':'3'*64,
                   'image_digests':{'catalog':'sha256:'+'4'*64}}
            plan={'scenario':'B4','private_catalog':True,'base_url':'http://127.0.0.1:18084',
                  'seed':53301,'trace_sha256':digest(source)}
            with patch('analysis.run.shutil.which',return_value='/bin/k6'):
                self.assertEqual(preflight(plan,source,facts,root),3)
                with self.assertRaises(ValueError):
                    preflight(plan | {'base_url':'http://192.168.110.92:8080'},source,facts,root)
                with self.assertRaises(ValueError):
                    preflight(plan | {'scenario':'B1'},source,facts,root)

    def test_campaign_preserves_overload_and_rejects_contract_or_dropped_iterations(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / 'source.csv'
            source.write_bytes(trace(53301, 'trace', 'quote', 2))
            plan = {'base_url': 'http://192.168.1.2:8081', 'seed': 53301, 'trace_sha256': digest(source),
                    'rate': 1, 'warmup_seconds': 1, 'measure_seconds': 1, 'vus': 6}
            facts = {'commit': '1' * 40, 'config_sha256': '2' * 64, 'protocol_sha256': '3' * 64,
                     'image_digests': {'order': 'sha256:' + '4' * 64}}
            cases = ((503, 0, None), (200, 0, 'HTTP 200 violated the application contract'),
                     (503, 1, 'k6 dropped iterations'))
            for attempt, (status, dropped, reason) in enumerate(cases):
                with self.subTest(status=status, dropped=dropped):
                    def performance(command, stdout, stderr, **options):
                        for index in range(2):
                            sample = {'request_index': index, 'status': status, 'contract_ok': False}
                            print('NT533_REQUEST ' + json.dumps(sample), file=stderr)
                        raw = {'type': 'Point', 'metric': 'dropped_iterations', 'data': {'value': dropped}}
                        Path(command[-2].split('=', 1)[1]).write_text(json.dumps(raw) + '\n')
                        return type('Result', (), {'returncode': 0})()
                    dest = root / f'attempt-a{attempt}'
                    with patch('analysis.run.shutil.which', return_value='/test/bin/k6'), \
                            patch('analysis.run.subprocess.run', side_effect=performance):
                        self.assertEqual(execute(plan, source, facts, dest), int(reason is not None))
                    receipt = json.loads((dest / 'manifest.json').read_text())
                    self.assertEqual(receipt.get('invalid_reason'), reason)
                    self.assertEqual(receipt['dropped_iterations'], dropped)
                    self.assertEqual(len((dest / 'requests.jsonl').read_text().splitlines()), 2)
