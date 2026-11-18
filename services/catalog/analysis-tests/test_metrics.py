import unittest

from analysis.analyze import latency
from analysis.mapping import fairness, remap


class MetricBoundaryTests(unittest.TestCase):
    def test_distribution_keeps_zero_members(self):
        self.assertEqual(fairness([100, 100, 100]), {'jain': 1, 'cv': 0})
        self.assertAlmostEqual(fairness([300, 0, 0])['jain'], 1 / 3)
        self.assertEqual(fairness([0, 0, 0]), {'jain': None, 'cv': None})

    def test_remap_at_equal_and_weighted_rates(self):
        before = {'a': 'I1', 'b': 'I2', 'c': 'I3', 'd': 'I2'}
        after = before | {'a': 'I4'}
        self.assertEqual(remap(before, after), .25)
        self.assertEqual(remap(before, after, {'a': 80, 'b': 10, 'c': 10, 'd': 0}), .8)
        with self.assertRaises(ValueError):
            remap(before, {'a': 'I4'})

    def test_percentile_empty_and_single_sample(self):
        self.assertIsNone(latency([])['p99'])
        self.assertEqual(latency([6.5]), {'samples': 1, 'p50': 6.5, 'p95': 6.5, 'p99': 6.5})
