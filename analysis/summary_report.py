"""Aggregate audited D9-D11 campaign ledgers into reproducible CSV/JSON summaries."""

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics

from analysis.mapping import fairness


RUN_FIELDS = (
    'day', 'run_id', 'scenario', 'profile', 'condition', 'algorithm', 'block',
    'target_rps', 'protocol_version', 'topology', 'accepted_requests', 'error_ratio',
    'success_rps', 'loadgen_p50_ms', 'loadgen_p95_ms', 'loadgen_p99_ms',
    'nginx_p50_ms', 'nginx_p95_ms', 'nginx_p99_ms',
    'wan_rtt_p95_ms', 'wan_jitter_ms', 'wan_loss_ratio', 'jain', 'cv', 'per_instance_json',
)


def _num(value):
    return None if value is None else float(value)


def _median(values):
    clean = [float(v) for v in values if v is not None]
    return statistics.median(clean) if clean else None


def flatten_run(day, entry):
    row = entry['row']
    metrics = entry['metrics']
    lat = metrics.get('latency_ms') or {}
    lg = lat.get('loadgen') or {}
    ng = lat.get('nginx') or {}
    wan = metrics.get('wan') or {}
    rtt = wan.get('rtt_ms') or {}
    instances = metrics.get('instances') or {}
    fair = fairness(list(instances.values())) if instances else {'jain': None, 'cv': None}
    return {
        'day': day,
        'run_id': entry['runId'],
        'scenario': row['scenario'],
        'profile': row['profile'],
        'condition': row['condition'],
        'algorithm': row['algorithm'],
        'block': row['block'],
        'target_rps': row['target_rps'],
        'protocol_version': row.get('protocol_version') or '',
        'topology': row.get('topology') or '',
        'accepted_requests': metrics['acceptedRequests'],
        'error_ratio': _num(metrics['errorRatio']),
        'success_rps': _num(metrics['successRps']),
        'loadgen_p50_ms': _num(lg.get('p50')),
        'loadgen_p95_ms': _num(lg.get('p95') if lg else metrics.get('p95')),
        'loadgen_p99_ms': _num(lg.get('p99')),
        'nginx_p50_ms': _num(ng.get('p50')),
        'nginx_p95_ms': _num(ng.get('p95')),
        'nginx_p99_ms': _num(ng.get('p99')),
        'wan_rtt_p95_ms': _num(rtt.get('p95')),
        'wan_jitter_ms': _num(wan.get('jitter_ms')),
        'wan_loss_ratio': _num(wan.get('loss_ratio')),
        'jain': fair['jain'],
        'cv': fair['cv'],
        'per_instance_json': json.dumps(instances, sort_keys=True),
    }


def summarize(audited_docs):
    if not audited_docs:
        raise ValueError('at least one audited day ledger is required')
    runs = []
    contrasts = []
    a4_entries = []
    recovery_rows = []
    days_seen = []
    for doc in audited_docs:
        if doc.get('exitCode') != 0:
            raise ValueError(f"audited day {doc.get('day')} did not pass")
        day = doc['day']
        days_seen.append(day)
        for entry in doc.get('results', []):
            runs.append(flatten_run(day, entry))
            if entry['row']['scenario'] == 'A2' and 'recovery' in entry['metrics']:
                rec = entry['metrics']['recovery']
                recovery_rows.append({
                    'run_id': entry['runId'],
                    'algorithm': entry['row']['algorithm'],
                    'block': entry['row']['block'],
                    'before_success_rps': rec.get('before_success_rps'),
                    'recovery_at': rec.get('recovery_at'),
                    'seconds_from_stop': rec.get('seconds_from_stop'),
                    'seconds_from_ready': rec.get('seconds_from_ready'),
                    'recovered_before_ready': rec.get('recovered_before_ready'),
                })
        contrasts.extend(doc.get('contrasts', []))
        a4_entries.extend(doc.get('a4', []))

    groups = defaultdict(list)
    for item in runs:
        groups[(item['scenario'], item['condition'], item['algorithm'])].append(item)

    cells = []
    for (scenario, condition, algorithm), items in sorted(groups.items()):
        cells.append({
            'scenario': scenario,
            'condition': condition,
            'algorithm': algorithm,
            'runs': len(items),
            'median_loadgen_p95_ms': _median(x['loadgen_p95_ms'] for x in items),
            'median_nginx_p95_ms': _median(x['nginx_p95_ms'] for x in items),
            'median_success_rps': _median(x['success_rps'] for x in items),
            'median_error_ratio': _median(x['error_ratio'] for x in items),
            'median_wan_rtt_p95_ms': _median(x['wan_rtt_p95_ms'] for x in items),
            'median_jain': _median(x['jain'] for x in items),
        })

    a4_summary = {}
    if a4_entries:
        by_variant = defaultdict(list)
        for item in a4_entries:
            by_variant[item['variant']].append(item['transitions'])
        for variant, trans_list in sorted(by_variant.items()):
            a4_summary[variant] = {
                edge: {
                    'median_unweighted': _median(t[edge]['unweighted'] for t in trans_list),
                    'median_weighted': _median(t[edge]['weighted'] for t in trans_list),
                    'seeds': len(trans_list),
                }
                for edge in ('3-4', '4-3', '3-3')
            }

    return {
        'days': sorted(days_seen),
        'total_performance_runs': len(runs),
        'cells': cells,
        'contrasts': contrasts,
        'a2_recovery': recovery_rows,
        'a4_summary': a4_summary,
        'runs': runs,
    }


def write_outputs(summary, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / 'campaign-runs.csv'
    with csv_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=RUN_FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(summary['runs'])
    json_path = output_dir / 'campaign-summary.json'
    payload = {k: v for k, v in summary.items() if k != 'runs'}
    json_path.write_text(json.dumps(payload, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    return {'csv': str(csv_path), 'json': str(json_path)}


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output_dir', type=Path)
    cli.add_argument('audited', nargs='+', type=Path)
    args = cli.parse_args()
    docs = [json.loads(p.read_text(encoding='utf-8')) for p in args.audited]
    summary = summarize(docs)
    paths = write_outputs(summary, args.output_dir)
    print(json.dumps({'days': summary['days'], 'runs': summary['total_performance_runs'], **paths}))


if __name__ == '__main__':
    main()
