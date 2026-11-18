import csv
import unittest

from analysis.mapping import SEEDS, remap, stable
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
