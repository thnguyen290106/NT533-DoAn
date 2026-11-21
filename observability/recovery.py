"""Report A2 recovery at the protocol's fixed ten-second boundaries."""

from datetime import timedelta

from analysis.analyze import latency
from observability.window import fault_events, measurement, utc


def recovery(rows, events, measure_start, *, pre_window=(30, 90), start_edge=90, end_edge=300, step=10):
    start=utc(measure_start)
    events=fault_events(list(events))
    if [row['action'] for row in events]!=['stop','start','ready'] or any(row['exit_code']!=0 for row in events):
        raise ValueError('A2 requires completed stop, start and readiness events')
    timestamps=[utc(row['timestamp_utc']) for row in events]
    if timestamps!=sorted(timestamps):
        raise ValueError('fault timestamps are out of order')
    rows=list(rows)

    def cohort(first,last):
        left=start+timedelta(seconds=first)
        right=start+timedelta(seconds=last)
        return measurement(rows,left.isoformat(),right.isoformat(),(right+timedelta(seconds=5)).isoformat())

    before=cohort(*pre_window)
    if not before['valid']:
        raise ValueError('pre-fault cohort has pending requests after drain')
    baseline=before['success_rps']
    consecutive=0
    recovered=None
    detail=[]
    for edge in range(start_edge,end_edge,step):
        window=cohort(edge,edge+step)
        records=window['latency_cohort']
        successful=[r['duration_ms'] for r in records if r['status']==200 and r['contract_ok']]
        p95=latency(successful)['p95']
        error_ratio=(len(records)-len(successful))/len(records) if records else None
        enough=len(successful)>=100
        rps=window['success_rps']
        passed=(baseline>0 and window['valid'] and enough and error_ratio<.01 and p95<500 and rps>=.95*baseline)
        detail.append({'first_second':edge,'success_samples':len(successful),'success_rps':rps,
                       'p95_wall_ms':p95,'error_ratio':error_ratio,'meets_recovery_slo':passed if enough else None})
        consecutive=consecutive+1 if passed else 0
        if consecutive==3 and recovered is None:
            recovered=start+timedelta(seconds=edge-2*step)
    return {'before_success_rps':baseline,'windows':detail,'recovery_at':recovered.isoformat() if recovered else None,
            'seconds_from_stop':(recovered-timestamps[0]).total_seconds() if recovered else None,
            'seconds_from_ready':(recovered-timestamps[2]).total_seconds() if recovered and recovered>=timestamps[2] else None,
            'recovered_before_ready':recovered<timestamps[2] if recovered else None}
