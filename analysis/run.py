"""Preflight and run a trace, preserving successful and invalid attempts."""

import argparse
import csv
from datetime import datetime, timezone
from hashlib import file_digest
from ipaddress import IPv4Address
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from urllib.parse import urlsplit

from analysis.trace import FIELDS


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = "NT533_REQUEST "


def digest(file):
    with file.open('rb') as stream:
        return file_digest(stream, 'sha256').hexdigest()


def validate_target(url):
    parsed = urlsplit(url)
    address = IPv4Address(parsed.hostname or "")
    if (parsed.scheme != "http" or not address.is_private or address.is_loopback
            or parsed.netloc != f"{address}:8081" or parsed.path or parsed.query or parsed.fragment):
        raise ValueError("base_url must be the private lab listener on port 8081")


def check_trace(file):
    with file.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(handle)
        if tuple(rows.fieldnames or ()) != FIELDS:
            raise ValueError("trace columns differ from the protocol")
        count = 0
        for row in rows:
            if (None in row or any(v is None for v in row.values()) or row['request_index'] != str(count)
                    or not re.fullmatch(r"[0-9a-f]{32}", row['request_id'])
                    or not re.fullmatch(r"c-[0-9a-f]{16}", row['client_id'])
                    or row['profile'] not in {'cpu-fixed', 'mixed-delay', 'mapping', 'quote'}
                    or any(re.search(r'[,"\r\n]', v) for v in row.values())):
                raise ValueError(f"invalid trace at index {count}")
            if row['profile'] == 'mixed-delay' and row['delay_class'] not in {'fast', 'slow'}:
                raise ValueError(f"invalid delay class at index {count}")
            if row['profile'] == 'quote' and (row['product_id'], row['quantity']) != ('P001', '2'):
                raise ValueError(f"invalid quote input at index {count}")
            count += 1
    if not count:
        raise ValueError("empty trace")
    return count


def workload_plan(plan, rows):
    if plan.get('dry_run') is True:
        return {'measure': {'executor': 'shared-iterations', 'vus': 1, 'iterations': rows, 'maxDuration': '120s'}}, {'measure': 0}, 135
    rate, warmup, measure, vus = (plan.get(key) for key in ('rate', 'warmup_seconds', 'measure_seconds', 'vus'))
    if any(type(v) is not int or v < 1 for v in (rate, warmup, measure, vus)) or rows != (warmup + measure) * rate:
        raise ValueError("campaign trace length must equal rate times planned phase seconds")
    shared = {'executor': 'constant-arrival-rate', 'rate': rate, 'timeUnit': '1s',
              'preAllocatedVUs': vus, 'maxVUs': vus, 'gracefulStop': '5s'}
    return ({'warmup': shared | {'duration': f'{warmup}s'},
             'measure': shared | {'duration': f'{measure}s', 'startTime': f'{warmup}s'}},
            {'warmup': 0, 'measure': warmup * rate}, warmup + measure + 15)


def samples(log):
    return [json.loads(line.split(SAMPLE, 1)[1]) for line in log.splitlines() if line.startswith(SAMPLE)]


def save_json(path, data):
    pending = path.with_suffix('.next')
    pending.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    pending.replace(path)


def preflight(plan, trace, facts, directory):
    validate_target(plan['base_url'])
    if not all(re.fullmatch(r'[0-9a-f]{64}', facts[key]) for key in ('config_sha256', 'protocol_sha256')):
        raise ValueError('missing configuration/protocol SHA-256')
    if not re.fullmatch(r'[0-9a-f]{40}', facts['commit']) or not facts['image_digests'] or not all(
        re.fullmatch(r'sha256:[0-9a-f]{64}', value) for value in facts['image_digests'].values()
    ):
        raise ValueError('missing checkout/image identity')
    if type(plan.get('seed')) is not int or not shutil.which('k6') or not shutil.which('git'):
        raise ValueError('seed, Git and k6 are required')
    if shutil.disk_usage(directory).free < plan.get('required_bytes', 0):
        raise ValueError('insufficient raw storage')
    if plan.get('trace_sha256') != digest(trace):
        raise ValueError('trace checksum changed')
    return check_trace(trace)


def execute(plan, trace, facts, dest):
    count = preflight(plan, trace, facts, dest.parent)
    scenarios, offsets, timeout = workload_plan(plan, count)
    dest.mkdir(exist_ok=False)
    local_trace = dest.resolve() / 'trace.csv'
    shutil.copyfile(trace, local_trace)
    manifest_path = dest / 'manifest.json'
    manifest = plan | facts | {'schema_version': 1, 'run_id': dest.name, 'scenarios': scenarios,
                              'offsets': offsets, 'started_utc': datetime.now(timezone.utc).isoformat(), 'status': 'running'}
    save_json(manifest_path, manifest)
    started = time.monotonic()
    command = ['k6', 'run', '--quiet', '--log-format', 'raw', '--out', 'json=' + str(dest.resolve() / 'k6-raw.json'),
               str(ROOT / 'load-tests' / 'workload.js')]
    with (dest / 'stdout.txt').open('w', encoding='utf-8') as out, (dest / 'stderr.txt').open('w', encoding='utf-8') as err:
        try:
            code = subprocess.run(command, stdout=out, stderr=err, timeout=timeout, check=False,
                                  env=os.environ | {'NT533_TRACE': str(local_trace), 'NT533_PLAN': json.dumps(manifest)}).returncode
        except subprocess.TimeoutExpired:
            code = 124
        except OSError as error:
            print(error, file=err)
            code = 126
    (dest / 'exit-code.txt').write_text(f'{code}\n', encoding='utf-8')
    try:
        rows = samples((dest / 'stderr.txt').read_text(encoding='utf-8'))
        indices = {row['request_index'] for row in rows}
        valid = code == 0 and len(rows) == count and indices == set(range(count)) and (dest / 'k6-raw.json').is_file()
        with (dest / 'requests.jsonl').open('w', encoding='utf-8') as output:
            for row in sorted(rows, key=lambda row: row['request_index']):
                print(json.dumps(row), file=output)
    except (ValueError, KeyError, TypeError) as error:
        valid, rows = False, []
        manifest['invalid_reason'] = str(error)
    manifest.update(status='valid' if valid else 'invalid', exit_code=code, completed=len(rows),
                    elapsed_seconds=round(time.monotonic() - started, 3))
    if not valid:
        manifest.setdefault('invalid_reason', 'k6 failed or trace and recorded requests differ')
    save_json(manifest_path, manifest)
    (dest / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in sorted(dest.iterdir()) if p.is_file()), encoding='utf-8')
    return 0 if valid else 1


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('trace', type=Path)
    cli.add_argument('plan', type=Path)
    cli.add_argument('facts', type=Path)
    cli.add_argument('directory', type=Path)
    cli.add_argument('--preflight-only', action='store_true')
    args = cli.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding='utf-8'))
        facts = json.loads(args.facts.read_text(encoding='utf-8'))
        if args.preflight_only:
            print(json.dumps({'trace_rows': preflight(plan, args.trace, facts, args.directory.parent), 'preflight': 'ok'}))
            return 0
        return execute(plan, args.trace, facts, args.directory)
    except (ValueError, OSError, KeyError, TypeError) as error:
        cli.exit(1, f'{error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
