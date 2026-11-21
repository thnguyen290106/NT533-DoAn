"""Evaluate Q05 pilot validity and select a reference rate from real receipts."""

from collections import defaultdict
from datetime import datetime, timedelta
import math

from analysis.analyze import duration, latency


LIMITS = {'cpu-fixed': 500, 'mixed-delay': 500, 'quote': 1_000}
RATES = tuple(10 * 2**step for step in range(9))


def nginx_timings(records, request_ids, peer, route):
    durations = {}
    for row in records:
        rid = row.get('request_id')
        if rid not in request_ids or row.get('peer_ip') != peer or row.get('route') != route or row.get('call_id'):
            continue
        if rid in durations or str(row.get('status')) != '200':
            raise ValueError(f'duplicate or inconsistent NGINX response for {rid}')
        durations[rid] = duration(float(row['request_time_s']) * 1000)
    if request_ids - durations.keys():
        raise ValueError('NGINX evidence is missing successful request IDs')
    return durations


def warmup_stability(rows, seconds, nginx_ms=None):
    warm = [row for row in rows if row['phase'] == 'warmup']
    starts = {row['phase_started_utc'] for row in warm}
    if len(starts) != 1:
        return {'stable': False, 'reason': 'Missing or ambiguous k6 phase start'}
    anchor = datetime.fromisoformat(starts.pop())
    successes = [row for row in warm if row['status'] == 200 and row['contract_ok']]
    windows = []
    for offset in (seconds - 60, seconds - 30):
        start = anchor + timedelta(seconds=offset)
        end = start + timedelta(seconds=30)
        cohort = [row for row in successes if start <= datetime.fromisoformat(row['started_utc']) < end]
        completed = sum(start <= datetime.fromisoformat(row['completed_utc']) < end for row in successes)
        client = latency(row['duration_ms'] for row in cohort)
        server = latency(nginx_ms[row['request_id']] for row in cohort) if nginx_ms is not None else None
        windows.append({'rps': completed / 30, 'p95': (server if server is not None else client)['p95'],
                        'loadgen_ms': client, 'nginx_ms': server})
    first, second = windows
    stable = (first['rps'] > 0 and abs(second['rps'] - first['rps']) <= .05 * first['rps'] and
              first['p95'] is not None and second['p95'] is not None and
              abs(second['p95'] - first['p95']) <= .10 * first['p95'])
    return {'stable': stable, 'p95_source': 'nginx' if nginx_ms is not None else 'loadgen', 'windows': windows}


def evaluate(profile, rate, samples, *, dropped, loadgen_ok, warmup_stable, measure_seconds=60):
    if profile not in LIMITS or rate not in (*RATES, 1, 2, 5) or type(dropped) is not int or dropped < 0:
        raise ValueError('unsupported pilot profile, rate or dropped count')
    if measure_seconds != 60:
        raise ValueError('Q05 pilot must measure for 60 seconds')
    chosen = [row for row in samples if row['phase'] == 'measure']
    ids = set()
    good = []
    bad_contract = False
    for row in chosen:
        rid, status, ok, elapsed = (row[k] for k in ('request_id','status','contract_ok','duration_ms'))
        if (not isinstance(rid,str) or rid in ids or type(status) is not int or type(ok) is not bool
                or type(elapsed) not in (int,float) or elapsed < 0 or not math.isfinite(elapsed)):
            raise ValueError('malformed or duplicate measurement sample')
        ids.add(rid)
        if status == 200:
            bad_contract |= not ok
            if ok:
                good.append(elapsed)
    target=rate*measure_seconds
    sent=len(chosen)
    reason=None
    if bad_contract:
        reason='HTTP 200 violated the application contract'
    elif sent < .99*target or sent > target or dropped or not loadgen_ok:
        reason='client could not produce the planned offered load'
    elif not warmup_stable:
        reason='warm-up is not stable'
    errors=(sent-len(good))/sent if sent else None
    p95=latency(good)['p95']
    passed=reason is None and errors is not None and errors < .01 and p95 is not None and p95 < LIMITS[profile]
    return {'profile':profile,'rate':rate,'sent':sent,'target':target,'dropped':dropped,'valid':reason is None,
            'invalid_reason':reason,'successful':len(good),'error_ratio':errors,'p95_wall_ms':p95,'slo_passed':passed}


def select_r_ref(profile, receipts):
    if profile not in LIMITS:
        raise ValueError('unknown profile')
    by_rate=defaultdict(list)
    for row in receipts:
        if row['profile']==profile and row['valid']:
            by_rate[row['rate']].append(row['slo_passed'])

    def status(rate):
        states=by_rate[rate]
        if states and all(states):
            return 'pass'
        if len(states)>=2 and not any(states):
            return 'fail'
        return 'open'

    candidates=(1,2,5,10) if status(10)=='fail' else RATES
    previous=None
    for rate in candidates:
        state=status(rate)
        if state=='open':
            return None
        if state=='fail':
            return {'R_ref':rate,'H':rate,'M':max(1,3*rate//5),'previous_pass_rps':previous} if previous is not None else None
        previous=rate
    return None
