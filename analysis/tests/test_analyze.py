import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.analyze import analyze


class AnalyzeTests(unittest.TestCase):
    def setUp(self):
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)

    def write(self, name, *rows):
        path = self.root / name
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return path

    def test_counts_errors_preserves_zeros_and_keeps_raw_latency_separate(self):
        requests = self.write("requests.jsonl", *[
            {"request_id": f"{i:032x}", "status": status, "contract_ok": ok,
             "duration_ms": latency, "instance_id": instance}
            for i, (status, ok, latency, instance) in enumerate([
                (200, True, 12.5, "O1"), (409, False, 5, "O2"),
                (200, False, 8, "O1"), (0, False, 1000, None),
            ])
        ])
        raw = self.write("k6-raw.json",
                         {"type": "Metric", "metric": "http_req_duration"},
                         {"type": "Point", "metric": "http_req_duration", "data": {"value": 10}},
                         {"type": "Point", "metric": "dropped_iterations", "data": {"value": 2}})
        logs = self.write("nginx.jsonl", {"request_id": "0" * 32}, {"request_id": "0" * 32})
        result = analyze(requests, ["O1", "O2", "O3"], raw=raw, nginx=logs)
        self.assertEqual((result["completed"], result["success"]), (4, 1))
        self.assertEqual(result["errors"], {"transport": 1, "http": 1, "contract": 1})
        self.assertEqual(result["per_instance_counts"], {"O1": 2, "O2": 1, "O3": 0})
        self.assertEqual(result["latency_ms"]["successful"]["p99"], 12.5)
        self.assertEqual(result["latency_ms"]["all_completed"]["p95"], 1000)
        self.assertEqual(result["k6"]["http_req_duration_ms"]["p95"], 10)
        self.assertEqual(result["k6"]["dropped_iterations"], 2)
        self.assertEqual(result["nginx_matched_requests"], 1)

    def test_empty_requests_preserve_all_instances_and_no_percentile(self):
        result = analyze(self.write("requests.jsonl"), ["I1", "I2"])
        self.assertEqual(result["per_instance_counts"], {"I1": 0, "I2": 0})
        self.assertIsNone(result["latency_ms"]["successful"]["p50"])
        self.assertIsNone(result["k6"])

    def test_duplicate_request_and_unknown_instance_are_rejected(self):
        row = {"request_id": "0" * 32, "status": 200, "contract_ok": True, "duration_ms": 1, "instance_id": "C1"}
        with self.assertRaisesRegex(ValueError, "duplicate request_id"):
            analyze(self.write("requests.jsonl", row, row), ["C1"])
        with self.assertRaisesRegex(ValueError, "unknown instance_id"):
            analyze(self.write("requests.jsonl", row), ["C2"])

    def test_measurement_excludes_warmup_and_keeps_drain_latency(self):
        def row(index, phase, started, finished):
            return {"request_id":f"{index:032x}", "phase":phase, "phase_started_utc":"2026-11-18T14:00:10Z",
                    "started_utc":f"2026-11-18T14:00:{started:02d}Z", "completed_utc":f"2026-11-18T14:00:{finished:02d}Z",
                    "status":200, "contract_ok":True, "duration_ms":1000*(finished-started), "instance_id":"C1"}
        requests=self.write("requests.jsonl",row(0,"warmup",8,9),row(1,"measure",10,11),row(2,"measure",19,22))
        receipt=analyze(requests,["C1","C2"],measure_seconds=10)
        self.assertEqual(receipt["completed"],2)
        self.assertEqual(receipt["measurement"]["success_rps"],.1)
        self.assertEqual(receipt["latency_ms"]["successful"]["p95"],3000)
        self.assertTrue(receipt["p99_small_sample"])
        with self.assertRaisesRegex(ValueError,"pending after drain"):
            analyze(requests,["C1","C2"],measure_seconds=10,drain_seconds=1)
