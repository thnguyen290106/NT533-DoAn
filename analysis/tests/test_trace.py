import csv
from hashlib import sha256
import unittest

from analysis.trace import client_ids, trace


def rows(payload):
    return list(csv.DictReader(payload.decode().splitlines()))


class TraceTests(unittest.TestCase):
    def test_hashes_indexes_and_rng_streams(self):
        mixed = trace(53301, "block1", "mixed-delay", 3000)
        plain = rows(trace(53301, "block1", "cpu-fixed", 3000))
        data = rows(mixed)
        self.assertEqual(mixed, trace(53301, "block1", "mixed-delay", 3000))
        self.assertNotIn(b"\r", mixed)
        self.assertEqual([r["client_id"] for r in data], [r["client_id"] for r in plain])
        self.assertEqual([int(r["request_index"]) for r in data], list(range(3000)))
        self.assertEqual(data[42]["request_id"], sha256(b"block1:42").hexdigest()[:32])
        self.assertEqual(len(set(client_ids(53301))), 1000)
        fast = sum(r["delay_class"] == "fast" for r in data)
        self.assertTrue(2250 < fast < 2550, fast)
