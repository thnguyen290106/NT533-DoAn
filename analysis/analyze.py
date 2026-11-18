"""Summarize a single run's client requests and optional k6/NGINX JSONL artifacts."""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re


REQUEST_ID = re.compile(r"[0-9a-f]{32}")
INSTANCE_ID = re.compile(r"(?:[CO][1-3]|I[1-4])")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def jsonl(path):
    with Path(path).open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                data = json.loads(line, object_pairs_hook=unique_object)
                if not isinstance(data, dict):
                    raise ValueError("expected an object")
            except ValueError as error:
                raise ValueError(f"{path}:{line_no}: {error}") from error
            yield data


def duration(value):
    if type(value) not in (int, float) or value < 0 or (type(value) is float and not math.isfinite(value)):
        raise ValueError("duration must be a finite nonnegative number in milliseconds")
    return value


def latency(values):
    ordered = sorted(values)
    return {
        "samples": len(ordered),
        **{f"p{p}": ordered[(p * len(ordered) + 99) // 100 - 1] if ordered else None
           for p in (50, 95, 99)},
    }


def k6_metrics(path):
    durations = []
    dropped = 0
    for sample in jsonl(path):
        metric = sample.get("metric")
        if sample.get("type") != "Point" or metric not in ("http_req_duration", "dropped_iterations"):
            continue
        point = sample.get("data")
        value = point.get("value") if isinstance(point, dict) else None
        if metric == "http_req_duration":
            durations.append(duration(value))
        else:
            if type(value) is not int or value < 0:
                raise ValueError("dropped_iterations must be a nonnegative count")
            dropped += value
    return {"http_req_duration_ms": latency(durations), "dropped_iterations": dropped}


def analyze(requests, instances, *, raw=None, nginx=None):
    counts = dict.fromkeys(instances, 0)
    if len(counts) != len(instances) or not counts or any(not INSTANCE_ID.fullmatch(i) for i in counts):
        raise ValueError("instances must contain unique Catalog, Inventory or Order identifiers")
    ids = set()
    successful = []
    completed = []
    errors = Counter({"transport": 0, "http": 0, "contract": 0})

    for row in jsonl(requests):
        request_id = row.get("request_id")
        if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id) or request_id in ids:
            raise ValueError(f"invalid or duplicate request_id: {request_id!r}")
        ids.add(request_id)
        status, contract_ok = row.get("status"), row.get("contract_ok")
        if type(status) is not int or (status != 0 and not 100 <= status <= 599) or type(contract_ok) is not bool:
            raise ValueError(f"invalid status or contract_ok for {request_id}")
        instance = row.get("instance_id")
        if instance is not None and (not isinstance(instance, str) or instance not in counts):
            raise ValueError(f"unknown instance_id for {request_id}: {instance!r}")
        elapsed = duration(row.get("duration_ms"))
        completed.append(elapsed)
        if instance is not None:
            counts[instance] += 1
        if status == 0:
            errors["transport"] += 1
        elif not 200 <= status < 300:
            errors["http"] += 1
        elif not contract_ok:
            errors["contract"] += 1
        else:
            successful.append(elapsed)

    matched = None
    if nginx is not None:
        nginx_ids = (row.get("request_id") for row in jsonl(nginx))
        matched = len({request_id for request_id in nginx_ids if isinstance(request_id, str) and request_id in ids})

    return {
        "completed": len(completed), "success": len(successful), "errors": dict(errors),
        "per_instance_counts": counts, "nginx_matched_requests": matched,
        "latency_ms": {"successful": latency(successful), "all_completed": latency(completed)},
        "k6": k6_metrics(raw) if raw is not None else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requests", type=Path, help="JSONL with request_id, status, contract_ok, duration_ms and optional instance_id")
    parser.add_argument("--instances", required=True, help="Comma-separated membership, including replicas with zero requests")
    parser.add_argument("--raw", type=Path, help="Optional k6 --out json JSONL")
    parser.add_argument("--nginx", type=Path, help="Optional NGINX JSONL access log for request-ID matching")
    args = parser.parse_args()
    try:
        result = analyze(args.requests, args.instances.split(","), raw=args.raw, nginx=args.nginx)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
