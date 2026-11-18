"""Generate a deterministic NT533 trace on LOADGEN."""

import argparse
import csv
from hashlib import sha256
import io
from pathlib import Path
import random


FIELDS = ("request_index", "request_id", "client_id", "effective_ip", "profile", "delay_class", "product_id", "quantity")
PROFILES = ("cpu-fixed", "mixed-delay", "quote")


def client_ids(seed):
    clients = ["c-" + sha256(f"{seed}:client:{j}".encode()).hexdigest()[:16] for j in range(1000)]
    if len(set(clients)) != 1000:
        raise ValueError("Client ID collision")
    return clients


def trace(seed, trace_id, profile, count):
    if profile not in PROFILES or count < 1:
        raise ValueError("Trace profile and positive row count required")
    client_rng, delay_rng = random.Random(seed), random.Random(seed + 100_000)
    clients = client_ids(seed)
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(FIELDS)
    for index in range(count):
        j = client_rng.randrange(1000)
        emit_id = sha256(f"{trace_id}:{index}".encode()).hexdigest()[:32]
        address = "" if profile == "quote" else f"10.{64 + j // 256}.{j % 256}.10"
        delay = ("fast" if delay_rng.random() < .8 else "slow") if profile == "mixed-delay" else ""
        writer.writerow((index, emit_id, clients[j], address, profile, delay,
                         "P001" if profile == "quote" else "", 2 if profile == "quote" else ""))
    return out.getvalue().encode("utf-8")


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--seed", type=int, required=True)
    cli.add_argument("--trace-id", required=True)
    cli.add_argument("--profile", choices=PROFILES, required=True)
    cli.add_argument("--count", type=int, required=True)
    cli.add_argument("--output", type=Path, required=True)
    args = cli.parse_args()
    payload = trace(args.seed, args.trace_id, args.profile, args.count)
    with args.output.open("xb") as output:
        output.write(payload)
    print(sha256(payload).hexdigest())


if __name__ == "__main__":
    main()
