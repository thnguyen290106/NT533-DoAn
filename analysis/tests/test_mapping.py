import csv
import unittest

from analysis.mapping import SEEDS, fairness, remap, stable
from analysis.trace import client_ids, trace


class MappingTests(unittest.TestCase):
    def test_seed_sets_nat_and_hot_client(self):
        sets = [set(client_ids(seed)) for seed in SEEDS]
        self.assertEqual(len(set.union(*sets)), 5000)
        rows = list(csv.DictReader(trace(53301, 'nat', 'mixed-delay', 2000, nat=True, hot_id=True).decode().splitlines()))
        self.assertEqual({'10.250.0.10'}, {row['effective_ip'] for row in rows})
        self.assertTrue(1500 < sum(row['client_id'] == client_ids(53301)[0] for row in rows) < 1700)

    def test_complete_stable_sweeps_and_lookup(self):
        before = {'a': 'I1', 'b': 'I3'}
        self.assertEqual(stable([before, before], ['a','b'], 3), before)
        self.assertEqual(remap(before, before), 0)
        with self.assertRaises(ValueError):
            stable([before, {'a': 'I1'}], ['a','b'], 3)
        with self.assertRaises(ValueError):
            stable([before, before], ['a','b','c'], 3)

    def test_weighted_unweighted_remap_and_fairness_zero_members(self):
        before = {'k0': 'I1', 'k1': 'I2', 'k2': 'I3', 'k3': 'I1'}
        after = {'k0': 'I4', 'k1': 'I2', 'k2': 'I3', 'k3': 'I1'}
        weights = {'k0': 800, 'k1': 100, 'k2': 50, 'k3': 50}
        self.assertAlmostEqual(remap(before, after), 0.25)
        self.assertAlmostEqual(remap(before, after, weights), 0.80)
        self.assertEqual(fairness([0, 0, 0]), {'jain': None, 'cv': None})
        self.assertAlmostEqual(fairness([100, 100, 100])['jain'], 1.0)
        self.assertAlmostEqual(fairness([100, 0, 0])['jain'], 1 / 3)
        with self.assertRaises(ValueError):
            remap(before, after, {'k0': -1, 'k1': 1, 'k2': 1, 'k3': 1})
