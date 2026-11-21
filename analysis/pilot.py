"""Execute the Q05 rate ladder serially, preserving every measurement."""

import argparse
from datetime import datetime, timezone
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from threading import Event, Thread
import time

from analysis.analyze import jsonl, k6_metrics, latency
from analysis.pilot_gate import RATES, evaluate, nginx_timings, select_r_ref, warmup_stability
from analysis.run import execute, save_json
from analysis.trace import trace
from analysis.wan import PROTOCOLS, TOPOLOGY, report as wan_report


def stamp():
    return datetime.now(timezone.utc).isoformat()


def host_stats(stop, samples):
    while not stop.is_set():
        sample={'utc':stamp()}
        for line in Path('/proc/meminfo').read_text().splitlines():
            if line.startswith(('MemAvailable:', 'MemTotal:', 'SwapFree:')):
                key,value,_=line.split()
                sample[key[:-1]+'_kib']=int(value)
        sample['cpu_jiffies']=[int(x) for x in Path('/proc/stat').read_text().splitlines()[0].split()[1:]]
        samples.append(sample)
        stop.wait(5)


def run_trial(folder, facts, profile, rate, duration, attempt, request_host=None):
    now=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run_id=f'PILOT-{profile}-RR-r{rate}-{now}-a{attempt}'
    import tempfile
    with tempfile.TemporaryDirectory(prefix='input-',dir=folder) as tmp:
        source=Path(tmp)/'trace.csv'
        source.write_bytes(trace(53301, f'pilot-{profile}-r{rate}', profile, rate*(duration+60)))
        work={
            'seed':53301,'algorithm':'rr','scenario':'PILOT','condition':profile,'rate':rate,'vus':rate*6,
            'warmup_seconds':duration,'measure_seconds':60,'cooldown_seconds':60,'base_url':facts['base_url'],
            'trace_sha256':sha256(source.read_bytes()).hexdigest(), 'cpu_iterations':facts['cpu_iterations'],
            'cpu_checksum':facts['cpu_checksum'],'required_bytes':512*1024**2,
        }
        output=folder/run_id
        stop=Event()
        stats=[]
        sampler=Thread(target=host_stats,args=(stop,stats),daemon=True)
        sampler.start()
        try:
            code=execute(work,source,facts['deployment'],output)
        finally:
            stop.set()
            sampler.join()
        finished=stamp()
        rows=list(jsonl(output/'requests.jsonl'))
        dropped=k6_metrics(output/'k6-raw.json')['dropped_iterations']
        successful=[row for row in rows if row['status']==200 and row['contract_ok']]
        measurement=[row for row in successful if row['phase']=='measure']
        evidence=['pilot-evaluation.json','loadgen-resources.json']
        timings=None
        wan=None
        evidence_error=None
        if facts['deployment'].get('protocol_version') in PROTOCOLS:
            start=json.loads((output/'manifest.json').read_text())['started_utc']
            access_log=output/'nginx.jsonl.gz'
            try:
                wan=wan_report(os.environ['NT533_WAN_SAMPLES'],start,finished)
                save_json(output/'wan.json',wan)
                evidence.append('wan.json')
                if facts['deployment']['topology']!=TOPOLOGY or not wan['samples']:
                    raise ValueError('missing WAN probe samples or unexpected topology')
                request_host({'run_id':run_id,'start_utc':start,'end_utc':finished})
                deadline=time.monotonic()+300
                while not access_log.is_file() and time.monotonic()<deadline:
                    time.sleep(1)
                if access_log.is_file():
                    evidence.append(access_log.name)
                route={'cpu-fixed':'/bench/catalog','mixed-delay':'/bench/inventory','quote':'/api/orders/quote'}[profile]
                with gzip.open(access_log,'rt',encoding='utf-8') as records:
                    timings=nginx_timings(map(json.loads,records),{row['request_id'] for row in successful},
                                          facts['deployment']['loadgen'],route)
            except (OSError, ValueError, KeyError, TypeError) as error:
                evidence_error='Q05 evidence unavailable: '+str(error)
        warm=warmup_stability(rows,duration,timings)
        if evidence_error:
            warm.update(stable=False,reason=evidence_error,p95_source='nginx')
        result=evaluate(profile,rate,rows,dropped=dropped,loadgen_ok=code==0,warmup_stable=warm['stable'])
        if evidence_error and result['invalid_reason']=='warm-up is not stable':
            result['invalid_reason']=evidence_error
        result.update(run_id=run_id,attempt=attempt,run_exit=code,warmup=warm,finished_at=finished,
                      protocol_version=facts['deployment'].get('protocol_version'),topology=facts['deployment'].get('topology'),
                      latency_ms={'loadgen':latency(row['duration_ms'] for row in measurement),
                                  'nginx':latency(timings[row['request_id']] for row in measurement) if timings is not None else None},
                      wan={key:value for key,value in wan.items() if key!='samples'} if wan else None,
                      min_loadgen_available_kib=min(x['MemAvailable_kib'] for x in stats))
        save_json(output/'pilot-evaluation.json',result)
        save_json(output/'loadgen-resources.json',stats)
        ledger=output/'SHA256SUMS'
        with ledger.open('a',encoding='utf-8') as handle:
            for name in evidence:
                handle.write(f'{sha256((output/name).read_bytes()).hexdigest()}  {name}\n')
        return result


def load_seed_trials(path, profile, deployment):
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(raw, list) or not raw:
        raise ValueError('seed trials must be a non-empty JSON list')
    seen = set()
    accepted = []
    for trial in raw:
        if not isinstance(trial, dict):
            raise ValueError('seed trial must be an object')
        rid = trial.get('run_id')
        if (not isinstance(rid, str) or not rid or rid in seen
                or trial.get('profile') != profile
                or trial.get('valid') is not True
                or trial.get('dropped') != 0
                or trial.get('rate') not in (*RATES, 1, 2, 5)
                or trial.get('attempt') not in (1, 2)
                or trial.get('protocol_version') != deployment.get('protocol_version')
                or trial.get('topology') != deployment.get('topology')):
            raise ValueError(f'incompatible or invalid seed trial: {rid!r}')
        seen.add(rid)
        accepted.append(trial)
    return accepted


def remaining_rates(profile, seeded_trials):
    by_rate = {}
    for trial in seeded_trials:
        if trial.get('profile') == profile and trial.get('valid'):
            by_rate.setdefault(trial['rate'], []).append(trial['slo_passed'])
    if 10 in by_rate and len(by_rate[10]) >= 2 and not any(by_rate[10]):
        ladder = [1, 2, 5]
    else:
        ladder = list(RATES)
    plan = []
    for rate in ladder:
        states = by_rate.get(rate, [])
        if states and all(states):
            continue
        if len(states) >= 2 and not any(states):
            continue
        if any(states) and not all(states):
            raise ValueError(f'inconsistent seeded SLO results at {rate} req/s')
        plan.append((rate, (2,) if len(states) == 1 else (1, 2)))
    return plan


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('folder', type=Path)
    cli.add_argument('profile', choices=('cpu-fixed', 'mixed-delay', 'quote'))
    cli.add_argument('warmup', type=int, choices=(120, 300))
    cli.add_argument('--seed-trials', type=Path, default=None,
                     help='Optional path to verified prior trials from the same deployment to resume from')
    args = cli.parse_args()
    folder, profile, warmup = args.folder, args.profile, args.warmup
    facts = json.loads((folder / 'facts.json').read_text())
    seeded = load_seed_trials(args.seed_trials, profile, facts['deployment']) if args.seed_trials else []
    state = {'profile': profile, 'status': 'running', 'started_at': stamp(), 'warmup_seconds': warmup, 'trials': list(seeded)}
    receipt = folder / 'progress.json'
    assert not receipt.exists()
    save_json(receipt, state)
    candidates = remaining_rates(profile, seeded)

    def request_host(evidence):
        state['host_evidence'] = evidence
        save_json(receipt, state)

    try:
        answer = select_r_ref(profile, state['trials'])
        if answer:
            state.update(status='verified', result=answer, finished_at=stamp())
            save_json(receipt, state)
            return
        while candidates:
            rate, attempts = candidates.pop(0)
            last_attempt = None
            for attempt in attempts:
                last_attempt = attempt
                state.update(current={'rate': rate, 'attempt': attempt, 'started_at': stamp()})
                save_json(receipt, state)
                trial = run_trial(folder, facts, profile, rate, warmup, attempt, request_host)
                state.pop('host_evidence', None)
                state['trials'].append(trial)
                save_json(receipt, state)
                time.sleep(60)
                if not trial['valid']:
                    raise RuntimeError(f"Invalid pilot trial {trial['run_id']}: {trial['invalid_reason']}")
                if trial['slo_passed']:
                    if attempt == 2:
                        raise RuntimeError(f'Inconsistent SLO across the two trials at {rate} req/s')
                    break
            if rate == 10 and last_attempt == 2 and candidates and candidates[0][0] == 20:
                candidates = [(r, (1, 2)) for r in (1, 2, 5)]
            answer = select_r_ref(profile, state['trials'])
            if answer:
                state.update(status='verified', result=answer, finished_at=stamp())
                save_json(receipt, state)
                return
        raise RuntimeError('No reference rate within the fixed Q05 rate ladder')
    except BaseException as error:
        state.update(status='blocked', error=str(error), finished_at=stamp())
        save_json(receipt, state)
        raise


if __name__ == '__main__':
    main()
