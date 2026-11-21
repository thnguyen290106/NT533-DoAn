"""Verify a run ledger and render its measured latency percentiles."""

import argparse
import json
from pathlib import Path

from analysis.analyze import analyze
from analysis.run import digest, save_json


def render(directory, instances):
    manifest = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['status'] != 'valid':
        raise ValueError(f"run {manifest['run_id']} is {manifest['status']}, raw evidence was retained")
    for line in (directory / 'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected, filename = line.split('  ', 1)
        if Path(filename).name != filename or digest(directory / filename) != expected:
            raise ValueError(f'SHA-256 verification failed: {filename}')
    raw, requests = directory / 'k6-raw.json', directory / 'requests.jsonl'
    summary = analyze(requests, instances, raw=raw,
                      measure_seconds=None if manifest.get('dry_run') else manifest['measure_seconds'],
                      drain_seconds=manifest.get('drain_seconds', 5))
    if summary['success'] == 0:
        raise ValueError('no successful samples to plot')
    summary['run_id'] = manifest['run_id']
    summary['sample_scope'] = 'dry run' if manifest.get('dry_run') else 'complete input artifact'
    summary['inputs'] = {file.name: digest(file) for file in (requests, raw)}
    save_json(directory / 'summary.json', summary)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(figsize=(10, 5.625), dpi=160)
    names = ('p50', 'p95', 'p99')
    values = [summary['latency_ms']['successful'][k] for k in names]
    axes.bar(names, values, color='#245c91')
    axes.set_ylabel('Client wall-clock latency (ms)')
    axes.set_title(f"{summary['run_id']} · {summary['sample_scope']} · n={summary['success']}")
    axes.grid(axis='y', alpha=.25)
    fig.tight_layout()
    fig.savefig(directory / 'latency.png', metadata={'Title': summary['run_id']})
    plt.close(fig)
    with (directory / 'SHA256SUMS').open('w', encoding='utf-8') as checksums:
        for file in sorted(directory.iterdir()):
            if file.is_file() and file.name != 'SHA256SUMS':
                checksums.write(f'{digest(file)}  {file.name}\n')
    return summary


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('directory', type=Path)
    cli.add_argument('--instances', required=True)
    args = cli.parse_args()
    try:
        print(json.dumps(render(args.directory, args.instances.split(','))))
    except (ValueError, OSError, KeyError) as error:
        cli.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
