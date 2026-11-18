from pathlib import Path
import unittest

from infra.routing import render


class RoutingTests(unittest.TestCase):
    def test_core_algorithms_share_every_other_setting(self):
        template = Path("infra/compose/nginx.conf").read_text(encoding="utf-8")
        self.assertEqual(render(template, "rr"), template)
        for name, directive in {"lc": "least_conn;", "iph": "ip_hash;"}.items():
            result = render(template, name)
            line = "        " + directive + "\n"
            self.assertEqual(result.count(line), 3)
            self.assertEqual(result.replace(line, ""), template)
