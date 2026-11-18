import unittest

from observability.window import counter_delta, fault_events, measurement


class WindowTests(unittest.TestCase):
    def test_warmup_and_drain_are_independent(self):
        def row(i, phase, start, end):
            return {'request_id': str(i), 'phase': phase, 'started_utc': f'2026-01-01T00:00:{start}Z',
                    'completed_utc': f'2026-01-01T00:00:{end}Z' if end else None, 'status': 200, 'contract_ok': True}
        rows = [row(0, 'warmup', '00', '11'), row(1, 'measure', '10', '15'), row(2, 'measure', '19', '21'),
                row(3, 'measure', '19.500', None), row(4, 'measure', '20', '21')]
        summary = measurement(rows, '2026-01-01T00:00:10Z', '2026-01-01T00:00:20Z', '2026-01-01T00:00:25Z')
        self.assertEqual([row['request_id'] for row in summary['latency_cohort']], ['1', '2', '3'])
        self.assertEqual(summary['success_rps'], .1)
        self.assertEqual(summary['pending_after_drain'], ['3'])
        self.assertFalse(summary['valid'])

    def test_missing_samples_and_resets_are_not_zero(self):
        self.assertIsNone(counter_delta(None, 2))
        self.assertIsNone(counter_delta(9, 2))
        self.assertEqual(counter_delta(2, 2), 0)
        self.assertEqual(counter_delta(2, 9), 7)

    def test_fault_requires_increasing_monotonic_timestamps(self):
        first = {'timestamp_utc': '2026-01-01T00:00:10Z', 'monotonic_ns': 1, 'action': 'stop',
                 'instance_id': 'I3', 'exit_code': 0}
        self.assertEqual(len(fault_events([first, first | {'action': 'start', 'monotonic_ns': 2}])), 2)
        with self.assertRaises(ValueError):
            fault_events([first, first])
