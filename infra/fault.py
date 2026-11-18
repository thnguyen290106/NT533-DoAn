"""Stop and restore only the project-owned I3 during a fault smoke or A2 run."""

import argparse
from datetime import datetime, timezone
import json
import re
import signal
import subprocess
import time


def docker(*args):
    return subprocess.run(['docker', *args], text=True, capture_output=True, timeout=20)


def owned_i3(project):
    if project != 'nt533-managed-v2' and not re.fullmatch(r'nt533-smoke-[A-Za-z0-9]{8}', project):
        raise ValueError('project is outside NT533 fault scope')
    found = docker('ps', '-q', '--filter', f'label=com.docker.compose.project={project}',
                   '--filter', 'label=com.docker.compose.service=inventory-3')
    ids = found.stdout.split()
    if found.returncode or len(ids) != 1 or not re.fullmatch('[a-f0-9]{12,64}', ids[0]):
        raise ValueError('running I3 is missing or ambiguous')
    return ids[0]


def fault(container, stop_at, start_at, stream):
    origin = time.monotonic()

    def emit(action, result):
        node = docker('inspect', '--format', '{{json .NetworkSettings.Networks}}', container)
        addresses = {name: data.get('IPAddress') for name, data in json.loads(node.stdout).items()} if node.returncode == 0 else None
        row = {'timestamp_utc': datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
               'monotonic_ns': time.monotonic_ns(), 'action': action, 'instance_id': 'I3',
               'container_id': container, 'addresses': addresses, 'exit_code': result.returncode}
        print(json.dumps(row), file=stream, flush=True)
        if result.returncode:
            raise RuntimeError(f'I3 {action} exited {result.returncode}: {result.stderr.strip()}')

    time.sleep(max(0, origin + stop_at - time.monotonic()))
    try:
        emit('stop', docker('stop', '-t', '0', container))
        time.sleep(max(0, origin + start_at - time.monotonic()))
    finally:
        emit('start', docker('start', container))
        deadline = time.monotonic() + 120
        healthy = 0
        while time.monotonic() < deadline:
            ready = docker('exec', container, 'wget', '-q', '-O', '/dev/null', 'http://127.0.0.1:8082/actuator/health/readiness')
            healthy = healthy + 1 if ready.returncode == 0 else 0
            if healthy == 3:
                emit('ready', ready)
                break
            time.sleep(1)
        else:
            raise TimeoutError('I3 restarted but did not become ready')


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('project')
    cli.add_argument('events')
    cli.add_argument('--smoke', action='store_true')
    args = cli.parse_args()
    if args.smoke and not args.project.startswith('nt533-smoke-'):
        cli.error('short fault smoke requires a disposable project')
    signal.signal(signal.SIGTERM, lambda *_: signal.raise_signal(signal.SIGINT))
    container = owned_i3(args.project)
    with open(args.events, 'x', encoding='utf-8') as stream:
        fault(container, *((0, 2) if args.smoke else (90, 150)), stream)


if __name__ == '__main__':
    main()
