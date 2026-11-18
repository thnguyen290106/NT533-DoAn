import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from analysis.run import check_trace, digest, execute, validate_target, workload_plan
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
