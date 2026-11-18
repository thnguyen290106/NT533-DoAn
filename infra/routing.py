"""Render the same NGINX configuration with a selected upstream algorithm."""

import argparse
from hashlib import sha256
from ipaddress import IPv4Address
from pathlib import Path
import re


ALGORITHMS = {"rr": "", "lc": "least_conn;", "iph": "ip_hash;",
              "ch-id": "hash $http_x_lab_client_id consistent;", "gh-id": "hash $http_x_lab_client_id;"}
ZONE = re.compile(r"^(        zone (?:catalog|inventory|order)_rr 64k;)$", re.MULTILINE)


def render(template: str, algorithm: str, peer: str | None = None, *, real_ip=False, inventory_members=3) -> str:
    advanced = algorithm in ("ch-id", "gh-id")
    if (advanced or real_ip) and peer is None:
        raise ValueError("ID/Real-IP routing requires a dedicated lab peer")
    if inventory_members not in (3, 4) or inventory_members == 4 and not advanced:
        raise ValueError("Four Inventory members are only supported by A4 ID variants")
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
    lab = lab.replace("@INVENTORY@", ALGORITHMS[algorithm]).replace("@I4@",
        "server inventory-4:8080 max_fails=1 fail_timeout=5s;" if inventory_members == 4 else "")
    ip_rules = (f"set_real_ip_from {address}/32;\n        real_ip_header X-Lab-Source-IP;\n"
                "        real_ip_recursive off;\n        if ($lab_ip_valid = 0) { return 400; }")
    lab = lab.replace("@REAL_IP@", ip_rules if real_ip else "")
    generation = sha256((result + lab).encode()).hexdigest()[:16]
    return result.rstrip()[:-1] + lab.replace("@GENERATION@", generation) + "}\n"


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("algorithm", choices=ALGORITHMS)
    cli.add_argument("--template", type=Path, default=Path(__file__).parent / "compose" / "nginx.conf")
    cli.add_argument("--lab-peer")
    cli.add_argument("--real-ip", action="store_true")
    cli.add_argument("--inventory-members", type=int, choices=(3, 4), default=3)
    args = cli.parse_args()
    print(render(args.template.read_text(encoding="utf-8"), args.algorithm, args.lab_peer,
                 real_ip=args.real_ip, inventory_members=args.inventory_members), end="")


if __name__ == "__main__":
    main()
