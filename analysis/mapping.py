"""Collect an A4 key mapping twice at one request per 100 ms."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import time
from urllib.request import build_opener, HTTPRedirectHandler, Request

from analysis.run import validate_target
from analysis.trace import client_ids


SEEDS = tuple(range(53401, 53406))
FIELDS = ('seed', 'variant', 'membership', 'sweep', 'client_id', 'instance_id', 'status', 'config_hash')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


def stable(sweeps, keys, membership):
    one, two = sweeps
    if set(one) != set(keys) or set(two) != set(keys) or one != two:
        raise ValueError('incomplete or unstable mapping across sweeps')
    if not set(one.values()) <= {f'I{n}' for n in range(1, membership + 1)}:
        raise ValueError('mapping used an out-of-membership instance')
    return one


def remap(before, after, weights=None):
    if not before or before.keys() != after.keys():
        raise ValueError('mapping snapshots must cover the same nonempty key set')
    changed = [key for key in before if before[key] != after[key]]
    if weights is None:
        return len(changed) / len(before)
    if before.keys() != weights.keys() or any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in weights.values()):
        raise ValueError('invalid key weights')
    total = sum(weights.values())
    return sum(weights[key] for key in changed) / total if total else None


def fairness(counts):
    if not counts or any(type(n) is not int or n < 0 for n in counts):
        raise ValueError('counts must include zero members and be nonnegative integers')
    total = sum(counts)
    if not total:
        return {'jain': None, 'cv': None}
    mean = total / len(counts)
    return {'jain': total * total / (len(counts) * sum(n * n for n in counts)),
            'cv': math.sqrt(sum((n - mean) ** 2 for n in counts) / len(counts)) / mean}


def collect(base, seed, variant, membership, generation, config_hash, output, *, concurrency=1, rate=10):
    validate_target(base)
    if seed not in SEEDS or variant not in ('ch-id', 'gh-id') or membership not in (3, 4):
        raise ValueError('unknown A4 keyset, variant or membership')
    if not re.fullmatch(r'[a-f0-9]{16}', generation) or not re.fullmatch(r'[a-f0-9]{64}', config_hash):
        raise ValueError('expected generation and config hash are required')
    if type(concurrency) is not int or concurrency < 1 or type(rate) is not int or rate < 1:
        raise ValueError('invalid A4 concurrency or rate')
    keys = sorted(client_ids(seed))
    opener = build_opener(NoRedirect())
    instances = {f'I{k}' for k in range(1, membership + 1)}

    def request(client, rid):
        req = Request(base + '/bench/inventory?profile=mapping', headers={
            'X-Request-ID': rid, 'X-Lab-Client-ID': client, 'Connection': 'close'})
        with opener.open(req, timeout=5) as response:
            body = json.load(response)
            instance = body.get('instanceId')
            if (response.status != 200 or response.headers.get('X-NT533-Generation') != generation
                    or response.headers.get('X-Request-ID') != rid or body.get('requestId') != rid
                    or body.get('profile') != 'mapping' or instance not in instances
                    or response.headers.get('X-Instance-ID') != instance):
                raise ValueError('invalid response or stale routing generation')
            return instance

    probe = sha256(f'{seed}:{variant}:{generation}:smoke'.encode()).hexdigest()[:32]
    request(keys[0], probe)
    sweeps = []
    with Path(output).open('x', encoding='utf-8', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(FIELDS)
        for n in (1, 2):
            snapshot = {}
            if concurrency == 1:
                start = time.monotonic()
                slot = 1 / rate
                for i, client in enumerate(keys):
                    scheduled = start + i * slot
                    time.sleep(max(0, scheduled - time.monotonic()))
                    if time.monotonic() - scheduled >= slot:
                        raise ValueError(f'cannot sustain {rate} requests/s with concurrency one')
                    rid = sha256(f'{seed}:{variant}:{membership}:{n}:{i}'.encode()).hexdigest()[:32]
                    try:
                        instance = request(client, rid)
                        if time.monotonic() - scheduled >= slot:
                            raise ValueError(f'response exceeded one {rate} requests/s slot')
                        snapshot[client] = instance
                        writer.writerow((seed, variant, membership, n, client, instance, 'ok', config_hash))
                    except (OSError, ValueError):
                        writer.writerow((seed, variant, membership, n, client, '', 'invalid', config_hash))
                        raise
            else:
                def task(item):
                    i, client = item
                    rid = sha256(f'{seed}:{variant}:{membership}:{n}:{i}'.encode()).hexdigest()[:32]
                    return client, request(client, rid)

                with ThreadPoolExecutor(max_workers=concurrency) as pool:
                    for client, instance in pool.map(task, enumerate(keys)):
                        snapshot[client] = instance
                        writer.writerow((seed, variant, membership, n, client, instance, 'ok', config_hash))
            sweeps.append(snapshot)
    return stable(sweeps, keys, membership)


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('url')
    cli.add_argument('seed', type=int, choices=SEEDS)
    cli.add_argument('variant', choices=('ch-id', 'gh-id'))
    cli.add_argument('membership', type=int, choices=(3,4))
    cli.add_argument('generation')
    cli.add_argument('config_hash')
    cli.add_argument('output')
    args = cli.parse_args()
    try:
        result = collect(args.url, args.seed, args.variant, args.membership, args.generation, args.config_hash, args.output)
    except (OSError, ValueError) as error:
        cli.exit(1, f'Snapshot invalid: {error}\n')
    print(json.dumps({'keys': len(result), 'membership': args.membership, 'sweeps': 2, 'stable': True}))


if __name__ == '__main__':
    main()
