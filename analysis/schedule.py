"""Construct the Q05 matrix before inspecting any campaign result."""

import argparse
from collections import Counter
import csv
from hashlib import sha256
import json
from pathlib import Path
from random import Random

from analysis.mapping import SEEDS
from analysis.trace import client_ids, trace


CORE = ('rr', 'lc', 'iph')
CELLS = (
    (9, 'B0', 'cpu-fixed', ('M', 'H'), ('rr',)),
    (9, 'B1', 'cpu-fixed', ('M', 'H'), CORE),
    (9, 'B2', 'mixed-delay', ('M', 'H'), CORE),
    (9, 'B3', 'quote', ('M',), CORE),
    (9, 'B4', 'cpu-fixed', ('M',), ('direct',)),
    (10, 'A1', 'mixed-delay', ('M',), CORE),
    (10, 'A3', 'mixed-delay', ('uniform', 'hot-id'), CORE + ('ch-id',)),
    (11, 'A2', 'mixed-delay', ('M',), CORE),
)
CONFIRMATIONS = (
    (10, 'B2', 'mixed-delay', ('H',), ('lc', 'rr')),
    (10, 'A3', 'mixed-delay', ('uniform',), ('ch-id', 'iph')),
)


def schedule(r_ref=None, *, fast_campaign=False):
    if r_ref is not None:
        if set(r_ref) != {'cpu-fixed','mixed-delay','quote'} or any(
            type(n) is not int or not 1 <= n <= 2560 for n in r_ref.values()
        ):
            raise ValueError('validated R_ref values are required for all three profiles')
    random = Random(53300)

    def permute(algorithms):
        return random.sample(algorithms, len(algorithms))

    paired = {block: permute(CORE) for block in range(1, 4)}
    performance = []
    for i, cell in enumerate(CELLS + CONFIRMATIONS):
        day, scenario, profile, conditions, algorithms = cell
        confirmation = i >= len(CELLS)
        for condition in conditions:
            for block in (4, 5) if confirmation else (1, 2, 3):
                linked = condition == 'M' and scenario in ('B2', 'A1', 'A2')
                trace_group = 'B2-A1-A2' if linked else 'B0-B1-B4' if scenario in ('B0', 'B1', 'B4') else scenario
                rate = None
                if r_ref is not None:
                    high = r_ref[profile]
                    rate = high if condition == 'H' else max(1, 3 * high // 5)
                for algorithm in paired[block] if linked else permute(algorithms):
                    measure = (55 if scenario == 'A2' else 15) if fast_campaign else (300 if scenario == 'A2' else 180)
                    warmup = 10 if fast_campaign else 120
                    cooldown = 3 if fast_campaign else 60
                    performance.append({'day':day,'scenario':scenario,'profile':profile,'condition':condition,
                                        'algorithm':algorithm,'block':block,'seed':53300+block,'confirm':confirmation,
                                        'trace_id':f'{trace_group}-{condition}-b{block}',
                                        'target_rps':rate,'vus':rate * 6 if rate is not None else None,
                                        'warmup_seconds':warmup,'measure_seconds':measure,
                                        'drain_seconds':5,'cooldown_seconds':cooldown})
    performance.sort(key=lambda row: row['day'])
    mapping = []
    for seed in SEEDS:
        for variant in permute(('gh-id','ch-id')):
            for membership_phase, members in (('initial',3),('expanded',4),('restored',3)):
                for sweep in (1,2):
                    mapping.append({'day':11,'scenario':'A4','seed':seed,'variant':variant,
                                    'phase':membership_phase,'members':members,'sweep':sweep,
                                    'target_rps':100 if fast_campaign else 10,
                                    'concurrency':8 if fast_campaign else 1,'keys':1000})
    assert Counter(r['day'] for r in performance)=={9:54,10:41,11:9} and len(mapping)==60
    return {'schedule_seed':53300,'status':'awaiting_pilot' if r_ref is None else 'rates_from_pilot',
            'performance':performance,'mapping':mapping}


def lock_schedule(plan, directory, warmup):
    if plan['status']!='rates_from_pilot' or warmup not in (10,15,120,300):
        raise ValueError('verified Q05 rates and a protocol warm-up are required')
    traces=directory/'traces'
    traces.mkdir(parents=True,exist_ok=False)
    checksums={}
    for run in plan['performance']:
        scenario=run['scenario']
        count=(warmup+run['measure_seconds'])*run['target_rps']
        variant='direct' if scenario=='B4' else str(run['measure_seconds'])
        name=f"{run['trace_id']}-{variant}.csv"
        if name not in checksums:
            payload=trace(run['seed'],run['trace_id'],run['profile'],count,
                          nat=scenario=='A3',hot_id=run['condition']=='hot-id',actual_ip=scenario=='B4')
            (traces/name).write_bytes(payload)
            checksums[name]=sha256(payload).hexdigest()
        run.update(warmup_seconds=warmup,trace_path=f'traces/{name}',trace_sha256=checksums[name])
    hot_requests=next(run['target_rps']*run['measure_seconds'] for run in plan['performance']
                      if run['scenario']=='A3' and run['condition']=='hot-id')
    for sweep in plan['mapping']:
        seed=sweep['seed']
        name=f'A4-keys-{seed}.txt'
        hot_name=f'A4-hot-{seed}.csv'
        weights_name=f'A4-weights-{seed}.csv'
        if name not in checksums:
            keys=sorted(client_ids(seed))
            hot=trace(seed,f'A4-hot-{seed}','mixed-delay',hot_requests,nat=True,hot_id=True)
            counts=Counter(r['client_id'] for r in csv.DictReader(hot.decode().splitlines()))
            weights=('client_id,weight\n'+''.join(f'{key},{counts[key]}\n' for key in keys)).encode()
            for filename,payload in ((name,('\n'.join(keys)+'\n').encode()),(hot_name,hot),(weights_name,weights)):
                (traces/filename).write_bytes(payload)
                checksums[filename]=sha256(payload).hexdigest()
        sweep.update(key_path=f'traces/{name}',key_sha256=checksums[name],
                     weight_trace=f'traces/{hot_name}',weight_trace_sha256=checksums[hot_name],
                     weight_path=f'traces/{weights_name}',weight_sha256=checksums[weights_name])
    for filename, rows in (('schedule.csv',plan['performance']),('mapping-schedule.csv',plan['mapping'])):
        with (directory/filename).open('x',encoding='utf-8',newline='') as output:
            writer=csv.DictWriter(output,fieldnames=list(rows[0]),lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    return checksums


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path)
    cli.add_argument('--pilot',type=Path)
    args=cli.parse_args()
    pilot=json.loads(args.pilot.read_text(encoding='utf-8')) if args.pilot else None
    if pilot is not None and (pilot.get('status')!='verified' or pilot.get('dropped')!=0):
        cli.error('pilot receipt must be verified with zero dropped iterations')
    data=schedule(pilot['r_ref'] if pilot is not None else None,
                  fast_campaign=bool(pilot and pilot.get('campaign_profile')=='fast-v4'))
    if pilot is not None:
        if pilot.get('protocol_version'):
            provenance={key:pilot[key] for key in ('protocol_version','topology','protocol_sha256')}
            data.update(provenance)
            for row in data['performance'] + data['mapping']:
                row.update(provenance)
        lock_schedule(data,args.output.parent,pilot['warmup_seconds'])
    with args.output.open('x',encoding='utf-8') as output:
        json.dump(data,output,indent=2)
        output.write('\n')


if __name__=='__main__':
    main()
