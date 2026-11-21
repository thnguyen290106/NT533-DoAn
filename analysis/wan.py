"""Record WAN probes on LOADGEN alongside one benchmark process."""
import ipaddress
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import statistics
import subprocess
import sys
from threading import Event, Thread

from analysis.analyze import latency


PROTOCOL = 'nt533-q05-remote-v2'
PROTOCOLS = {PROTOCOL, 'nt533-q05-remote-v3', 'nt533-q05-remote-v4'}
TOPOLOGY = 'remote-zerotier'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sample(stop, host, output):
    while not stop.is_set():
        result = {'utc': stamp()}
        try:
            probe = subprocess.run(['/usr/bin/ping', '-n', '-c', '1', '-W', '1', host],
                                   text=True, capture_output=True, timeout=3, env={'LC_ALL': 'C'})
            match = re.search(r'time[=<]([0-9.]+)\s*ms', probe.stdout)
            result.update(exit_code=probe.returncode, rtt_ms=float(match[1]) if match else None)
        except subprocess.TimeoutExpired:
            result.update(exit_code=124, rtt_ms=None)
        result['ram_kib'] = {line.split(':')[0]: int(line.split()[1]) for line in
                            Path('/proc/meminfo').read_text().splitlines()
                            if line.startswith(('MemAvailable:', 'MemTotal:', 'SwapFree:'))}
        result['cpu_jiffies'] = [int(item) for item in Path('/proc/stat').read_text().splitlines()[0].split()[1:]]
        print(json.dumps(result), file=output, flush=True)
        stop.wait(1)


def report(path, start, end):
    # Read complete lines only while the native sampler is still writing.
    content = Path(path).read_text(encoding='utf-8')
    samples = [json.loads(line) for line in content[:content.rfind('\n') + 1].splitlines()]
    start, end = datetime.fromisoformat(start), datetime.fromisoformat(end)
    selected = [row for row in samples if start <= datetime.fromisoformat(row['utc']) < end]
    replies = [row['rtt_ms'] for row in selected if row['exit_code'] == 0 and row['rtt_ms'] is not None]
    lost = sum(row['exit_code'] == 1 for row in selected)
    sent = len(replies) + lost
    return {'samples': selected, 'rtt_ms': latency(replies),
            'jitter_ms': statistics.pstdev(replies) if replies else None,
            'sent': sent, 'received': len(replies), 'lost': lost,
            'loss_ratio': lost / sent if sent else None, 'probe_errors': len(selected) - sent}


def main():
    host, filename, separator, *command = sys.argv[1:]
    if separator != '--' or not ipaddress.IPv4Address(host).is_private or not command:
        raise ValueError('Expected the private benchmark target and command')
    stop = Event()
    with Path(filename).open('x', encoding='utf-8') as log:
        observer = Thread(target=sample, args=(stop, host, log))
        observer.start()
        try:
            return subprocess.run(command, check=False).returncode
        finally:
            stop.set()
            observer.join()


if __name__ == '__main__':
    sys.exit(main())
