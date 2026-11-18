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

    def test_hash_key_variants_differ_only_in_consistency(self):
        template = Path("infra/compose/nginx.conf").read_text(encoding="utf-8")
        with self.assertRaises(ValueError):
            render(template, "ch-id")
        with self.assertRaises(ValueError):
            render(template, "ch-id", "0.0.0.0")
        ch = render(template, "ch-id", "192.168.110.62")
        gh = render(template, "gh-id", "192.168.110.62")
        self.assertEqual(ch.replace("$http_x_lab_client_id consistent;", "$http_x_lab_client_id;"), gh)
        self.assertIn('"~^c-[0-9a-f]{16}$" 1;', gh)
        self.assertIn("192.168.110.62/32 1;", gh)
        self.assertNotIn("listen 8081;", render(template, "rr"))
