import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from analysis import pilot


def _trial(rate, passed, *, attempt=1, valid=True, dropped=0, profile='cpu-fixed',
           protocol='nt533-q05-remote-v3', topology='remote-zerotier'):
    return {
        'run_id': f'PILOT-{profile}-RR-r{rate}-20261120T170000000000Z-a{attempt}',
        'profile': profile,
        'rate': rate,
        'attempt': attempt,
        'valid': valid,
        'dropped': dropped,
        'slo_passed': passed,
        'protocol_version': protocol,
        'topology': topology,
        'source_unit': 'nt533-d8-pilot-69da32499e3d-cpu-fixed-39c7952e.service',
    }


class PilotResumeTests(unittest.TestCase):
    def test_default_ladder_starts_at_ten_without_seed(self):
        plan = pilot.remaining_rates('cpu-fixed', [])
        self.assertEqual([r for r, _ in plan[:4]], [10, 20, 40, 80])
        self.assertTrue(all(attempts == (1, 2) for _, attempts in plan))

    def test_resume_skips_verified_10_20_40_and_starts_at_80(self):
        seeded = [_trial(10, True), _trial(20, True), _trial(40, True)]
        plan = pilot.remaining_rates('cpu-fixed', seeded)
        self.assertEqual(plan[0], (80, (1, 2)))
        partial = seeded + [_trial(80, False, attempt=1)]
        self.assertEqual(pilot.remaining_rates('cpu-fixed', partial)[0], (80, (2,)))

    def test_seed_validation_rejects_invalid_or_mismatched_trials(self):
        dep = {'protocol_version': 'nt533-q05-remote-v3', 'topology': 'remote-zerotier'}
        bad_cases = [
            [],
            [_trial(80, False, valid=False)],
            [_trial(10, True, dropped=1)],
            [_trial(10, True, profile='mixed-delay')],
            [_trial(10, True, protocol='nt533-q05-remote-v2')],
            [_trial(10, True, topology='lan')],
            [_trial(10, True), _trial(10, True)],  # duplicate run_id
        ]
        with TemporaryDirectory() as tmp:
            for idx, payload in enumerate(bad_cases):
                path = Path(tmp) / f'bad-{idx}.json'
                path.write_text(json.dumps(payload), encoding='utf-8')
                with self.subTest(idx=idx), self.assertRaises(ValueError):
                    pilot.load_seed_trials(path, 'cpu-fixed', dep)

    def test_main_resumes_at_80_and_locks_r_ref_while_default_runs_full_ladder(self):
        dep = {'protocol_version': 'nt533-q05-remote-v3', 'topology': 'remote-zerotier'}
        facts = {'base_url': 'http://192.168.51.150:8081', 'cpu_iterations': 512000, 'cpu_checksum': '0' * 64, 'deployment': dep}

        # 1. Default mode (no --seed-trials): runs 10, 20, 40, 80(a1), 80(a2)
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'facts.json').write_text(json.dumps(facts), encoding='utf-8')
            called = []

            def fake_trial(_folder, _facts, profile, rate, duration, attempt, request_host=None):
                called.append((rate, attempt))
                return _trial(rate, passed=rate < 80, attempt=attempt, profile=profile)

            with patch.object(pilot, 'run_trial', side_effect=fake_trial), \
                 patch.object(pilot.time, 'sleep'), \
                 patch.object(sys, 'argv', ['pilot.py', str(folder), 'cpu-fixed', '300']):
                pilot.main()

            self.assertEqual(called, [(10, 1), (20, 1), (40, 1), (80, 1), (80, 2)])
            progress = json.loads((folder / 'progress.json').read_text(encoding='utf-8'))
            self.assertEqual(progress['status'], 'verified')
            self.assertEqual(progress['result'], {'R_ref': 80, 'H': 80, 'M': 48, 'previous_pass_rps': 40})

        # 2. Resumed mode (--seed-trials with 10, 20, 40): runs ONLY 80(a1), 80(a2)
        with TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / 'facts.json').write_text(json.dumps(facts), encoding='utf-8')
            seed_path = folder / 'seed-trials.json'
            seed_path.write_text(json.dumps([_trial(10, True), _trial(20, True), _trial(40, True)]), encoding='utf-8')
            called = []

            def fake_trial(_folder, _facts, profile, rate, duration, attempt, request_host=None):
                called.append((rate, attempt))
                return _trial(rate, passed=rate < 80, attempt=attempt, profile=profile)

            with patch.object(pilot, 'run_trial', side_effect=fake_trial), \
                 patch.object(pilot.time, 'sleep'), \
                 patch.object(sys, 'argv', ['pilot.py', str(folder), 'cpu-fixed', '300', '--seed-trials', str(seed_path)]):
                pilot.main()

            self.assertEqual(called, [(80, 1), (80, 2)])
            progress = json.loads((folder / 'progress.json').read_text(encoding='utf-8'))
            self.assertEqual(progress['status'], 'verified')
            self.assertEqual(len(progress['trials']), 5)
            self.assertEqual(progress['result'], {'R_ref': 80, 'H': 80, 'M': 48, 'previous_pass_rps': 40})


if __name__ == '__main__':
    unittest.main()
