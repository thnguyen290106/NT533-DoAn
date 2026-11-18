"""Render the same NGINX configuration with a selected upstream algorithm."""

import argparse
from ipaddress import IPv4Address
from pathlib import Path
import re


ALGORITHMS = {"rr": "", "lc": "least_conn;", "iph": "ip_hash;",
              "ch-id": "hash $http_x_lab_client_id consistent;", "gh-id": "hash $http_x_lab_client_id;"}
ZONE = re.compile(r"^(        zone (?:catalog|inventory|order)_rr 64k;)$", re.MULTILINE)


def render(template: str, algorithm: str, peer: str | None = None) -> str:
    advanced = algorithm in ("ch-id", "gh-id")
    if advanced and peer is None:
        raise ValueError("ID routing requires a dedicated lab peer")
    directive = "" if advanced else ALGORITHMS[algorithm]
    result, upstreams = ZONE.subn(lambda m: m[0] + ("\n        " + directive if directive else ""), template)
    if upstreams != 3:
        raise ValueError(f"Expected three Catalog/Inventory/Order upstreams, found {upstreams}")
    if peer is None:
        return result
    address = IPv4Address(peer)
    if not address.is_private or address.is_loopback or address.is_unspecified or address.is_link_local:
        raise ValueError("Lab peer must be one private IPv4 address")
    lab = (Path(__file__).parent / "compose" / "lab.conf.tpl").read_text(encoding="utf-8")
    lab = lab.replace("@PEER@", f"{address}/32").replace("@CATALOG@", directive)
    lab = lab.replace("@INVENTORY@", ALGORITHMS[algorithm])
    return result.rstrip()[:-1] + lab + "}\n"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("algorithm", choices=ALGORITHMS)
    cli.add_argument("--template", type=Path, default=Path(__file__).parent / "compose" / "nginx.conf")
    cli.add_argument("--lab-peer")
    args = cli.parse_args()
    print(render(args.template.read_text(encoding="utf-8"), args.algorithm, args.lab_peer), end="")


if __name__ == "__main__":
    main()
