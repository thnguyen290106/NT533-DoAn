import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from analysis.summary_report import summarize, write_outputs


def _run(run_id, scenario, profile, condition, algorithm, block, p95, nginx_p95=40, instances=None):
    return {
        'runId': run_id,
        'row': {
            'scenario': scenario,
            'profile': profile,
            'condition': condition,
            'algorithm': algorithm,
            'block': block,
            'target_rps': 48,
            'protocol_version': 'nt533-q05-remote-v3',
            'topology': 'remote-zerotier',
        },
        'metrics': {
            'p95': p95,
            'successRps': 48.0,
            'errorRatio': 0.0,
            'acceptedRequests': 8640,
            'instances': instances or {'C1': 2880, 'C2': 2880, 'C3': 2880},
            'latency_ms': {
                'loadgen': {'p50': 50, 'p95': p95, 'p99': p95 + 20, 'samples': 8640},
                'nginx': None if nginx_p95 is None else {'p50': 35, 'p95': nginx_p95, 'p99': nginx_p95 + 10, 'samples': 8640},
            },
            'wan': {'rtt_ms': {'p50': 11.5, 'p95': 15.0, 'p99': 20.0, 'samples': 180}, 'jitter_ms': 1.8, 'lost': 0, 'sent': 180, 'loss_ratio': 0.0},
        },
    }


class SummaryReportTests(unittest.TestCase):
    def test_aggregates_d9_d10_d11_and_writes_csv_json(self):
        d9 = {
            'day': 9, 'exitCode': 0,
            'results': [
                _run('B1-1', 'B1', 'cpu-fixed', 'M', 'rr', 1, 64),
                _run('B4-1', 'B4', 'cpu-fixed', 'M', 'direct', 1, 52, nginx_p95=None, instances={'C1': 8640}),
            ],
        }
        d10 = {
            'day': 10, 'exitCode': 0,
            'results': [
                _run('A3-1', 'A3', 'mixed-delay', 'uniform', 'iph', 1, 220, nginx_p95=205, instances={'I1': 8640, 'I2': 0, 'I3': 0}),
            ],
            'contrasts': [{'scenario': 'A3', 'condition': 'uniform', 'baseline': 'iph', 'candidate': 'ch-id', 'meanMs': -120.0, 'percentile95Ms': [-140.0, -100.0]}],
        }
        a2 = _run('A2-1', 'A2', 'mixed-delay', 'M', 'lc', 1, 95, nginx_p95=80, instances={'I1': 4320, 'I2': 4320, 'I3': 0})
        a2['metrics']['recovery'] = {
            'before_success_rps': 48.0,
            'recovery_at': '2026-11-21T01:02:00+00:00',
            'seconds_from_stop': 20.0,
            'seconds_from_ready': 0.0,
            'recovered_before_ready': False,
        }
        d11 = {
            'day': 11, 'exitCode': 0,
            'results': [a2],
            'a4': [{
                'seed': 53401, 'variant': 'ch-id',
                'transitions': {
                    '3-4': {'unweighted': 0.25, 'weighted': 0.20},
                    '4-3': {'unweighted': 0.25, 'weighted': 0.20},
                    '3-3': {'unweighted': 0.0, 'weighted': 0.0},
                },
            }],
        }

        summary = summarize([d9, d10, d11])
        self.assertEqual(summary['days'], [9, 10, 11])
        self.assertEqual(summary['total_performance_runs'], 4)
        self.assertEqual(len(summary['contrasts']), 1)
        self.assertEqual(len(summary['a2_recovery']), 1)
        self.assertAlmostEqual(summary['a4_summary']['ch-id']['3-4']['median_unweighted'], 0.25)

        with TemporaryDirectory() as tmp:
            out = write_outputs(summary, Path(tmp))
            with Path(out['csv']).open(encoding='utf-8') as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 4)
            b4 = next(r for r in rows if r['run_id'] == 'B4-1')
            self.assertEqual(b4['nginx_p95_ms'], '')
            a3 = next(r for r in rows if r['run_id'] == 'A3-1')
            self.assertAlmostEqual(float(a3['jain']), 1 / 3, places=5)
            self.assertIn('"I2": 0', a3['per_instance_json'])

    def test_rejects_failed_day(self):
        with self.assertRaises(ValueError):
            summarize([{'day': 9, 'exitCode': 1, 'results': []}])


if __name__ == '__main__':
    unittest.main()
