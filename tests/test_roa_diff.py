import json
import os
import unittest

from roa_diff import Vrp, diff, filter_vrps, load_vrps, parse_asn

HERE = os.path.dirname(os.path.abspath(__file__))


def load(name):
    with open(os.path.join(HERE, "..", "examples", name), encoding="utf-8") as fh:
        return load_vrps(json.load(fh))


class RoaDiffTest(unittest.TestCase):
    def test_parse_asn(self):
        self.assertEqual(parse_asn("AS64500"), 64500)
        self.assertEqual(parse_asn("as64500"), 64500)
        self.assertEqual(parse_asn(64500), 64500)

    def test_missing_max_length_defaults_to_prefix_length(self):
        vrps = load_vrps({"roas": [{"asn": "AS1", "prefix": "192.0.2.0/24", "ta": "arin"}]})
        self.assertEqual(vrps, {Vrp(1, "192.0.2.0/24", 24, "arin")})

    def test_diff(self):
        added, removed, changed = diff(load("old.json"), load("new.json"))
        self.assertEqual(added, [Vrp(64504, "203.0.113.0/24", 24, "apnic")])
        self.assertEqual(removed, [Vrp(64503, "203.0.113.0/24", 24, "apnic")])
        self.assertEqual(len(changed), 1)
        old, new = changed[0]
        self.assertEqual((old.prefix, old.max_length, new.max_length), ("198.51.100.0/22", 22, 24))

    def test_no_changes(self):
        self.assertEqual(diff(load("old.json"), load("old.json")), ([], [], []))

    def test_filter(self):
        vrps = filter_vrps(load("old.json"), set(), {"ripe"})
        self.assertEqual({v.asn for v in vrps}, {64501, 64502})


if __name__ == "__main__":
    unittest.main()
