"""Render the same NGINX configuration with a selected upstream algorithm."""

import argparse
from pathlib import Path
import re


ALGORITHMS = {"rr": "", "lc": "least_conn;", "iph": "ip_hash;"}
ZONE = re.compile(r"^(        zone (?:catalog|inventory|order)_rr 64k;)$", re.MULTILINE)


def render(template: str, algorithm: str) -> str:
    directive = ALGORITHMS[algorithm]
    result, upstreams = ZONE.subn(lambda m: m[0] + ("\n        " + directive if directive else ""), template)
    if upstreams != 3:
        raise ValueError(f"Expected three Catalog/Inventory/Order upstreams, found {upstreams}")
    return result


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("algorithm", choices=ALGORITHMS)
    cli.add_argument("--template", type=Path, default=Path(__file__).parent / "compose" / "nginx.conf")
    args = cli.parse_args()
    print(render(args.template.read_text(encoding="utf-8"), args.algorithm), end="")


if __name__ == "__main__":
    main()
