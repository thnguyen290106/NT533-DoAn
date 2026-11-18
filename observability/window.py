"""Apply NT533 UTC measurement and drain windows to request events."""

from datetime import datetime, timedelta
import math


def utc(value):
    if not isinstance(value, str):
        raise ValueError('timestamp must be ISO-8601 UTC')
    result = datetime.fromisoformat(value)
    if result.utcoffset() != timedelta(0):
        raise ValueError('timestamp must be ISO-8601 UTC')
    return result


def measurement(rows, start_utc, end_utc, drain_utc):
    start, end, drain = map(utc, (start_utc, end_utc, drain_utc))
    if not start < end <= drain:
        raise ValueError('invalid measurement/drain boundaries')
    started, completed, timed_out = [], [], []
    seen = set()
    for row in rows:
        if row['request_id'] in seen:
            raise ValueError('duplicate request_id')
        seen.add(row['request_id'])
        request_start = utc(row['started_utc'])
        request_end = utc(row['completed_utc']) if row.get('completed_utc') else None
        if request_end is not None and request_end < request_start:
            raise ValueError('request ended before it started')
        if row['phase'] != 'measure' or not start <= request_start < end:
            continue
        started.append(row)
        if request_end is None or request_end > drain:
            timed_out.append(row['request_id'])
        elif request_end < end and row['contract_ok'] and 200 <= row['status'] < 300:
            completed.append(row)
    return {'latency_cohort': started, 'success_completion_count': len(completed),
            'success_rps': len(completed) / (end - start).total_seconds(),
            'pending_after_drain': timed_out, 'valid': not timed_out}


def counter_delta(before, after):
    if before is None or after is None:
        return None
    if any(type(v) not in (int, float) or not math.isfinite(v) or v < 0 for v in (before, after)):
        raise ValueError('counter must be finite and nonnegative')
    return after - before if after >= before else None


def fault_events(rows):
    prior = -1
    for row in rows:
        utc(row['timestamp_utc'])
        ns = row['monotonic_ns']
        if (type(ns) is not int or ns <= prior or row['action'] not in ('stop', 'start', 'ready')
                or row['instance_id'] != 'I3' or type(row['exit_code']) is not int):
            raise ValueError('fault event identity, ordering or exit code is invalid')
        prior = ns
    return rows
