#!/usr/bin/env python3
"""Diff two RPKI ROA exports.

Reads the JSON that Routinator (``routinator vrps -f json``) and rpki-client
(``rpki-client -j``) produce and prints the VRPs that were added, removed or
had their maxLength changed between the two.
"""

import argparse
import ipaddress
import json
import sys
from typing import Iterable, NamedTuple


class Vrp(NamedTuple):
    asn: int
    prefix: str
    max_length: int
    ta: str


def parse_asn(value) -> int:
    if isinstance(value, int):
        return value
    value = str(value).strip().upper()
    if value.startswith("AS"):
        value = value[2:]
    return int(value)


def load_vrps(doc: dict) -> set[Vrp]:
    vrps = set()
    for roa in doc.get("roas", []):
        network = ipaddress.ip_network(roa["prefix"], strict=False)
        max_length = int(roa.get("maxLength", network.prefixlen))
        vrps.add(Vrp(parse_asn(roa["asn"]), str(network), max_length, roa.get("ta", "")))
    return vrps


def sort_key(vrp: Vrp):
    network = ipaddress.ip_network(vrp.prefix)
    return (network.version, network, vrp.asn, vrp.max_length)


def diff(old: set[Vrp], new: set[Vrp]):
    """Return (added, removed, changed).

    A (prefix, asn) pair that exists on both sides with a different
    maxLength is reported as changed rather than as an add and a remove.
    """
    added = new - old
    removed = old - new

    old_by_key = {(v.prefix, v.asn): v for v in removed}
    new_by_key = {(v.prefix, v.asn): v for v in added}
    changed = []
    for key in sorted(old_by_key.keys() & new_by_key.keys(), key=lambda k: sort_key(old_by_key[k])):
        changed.append((old_by_key[key], new_by_key[key]))
        added.discard(new_by_key[key])
        removed.discard(old_by_key[key])

    return sorted(added, key=sort_key), sorted(removed, key=sort_key), changed


def filter_vrps(vrps: Iterable[Vrp], asns: set[int], tas: set[str]) -> set[Vrp]:
    return {
        v for v in vrps
        if (not asns or v.asn in asns) and (not tas or v.ta.lower() in tas)
    }


def read_json(path: str) -> dict:
    if path == "-":
        return json.load(sys.stdin)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Diff two RPKI ROA exports.")
    parser.add_argument("old", help="older export (JSON, - for stdin)")
    parser.add_argument("new", help="newer export (JSON)")
    parser.add_argument("--asn", action="append", default=[], help="only this origin AS (repeatable)")
    parser.add_argument("--ta", action="append", default=[], help="only this trust anchor (repeatable)")
    parser.add_argument("--json", action="store_true", help="print the diff as JSON")
    args = parser.parse_args(argv)

    asns = {parse_asn(a) for a in args.asn}
    tas = {t.lower() for t in args.ta}
    old = filter_vrps(load_vrps(read_json(args.old)), asns, tas)
    new = filter_vrps(load_vrps(read_json(args.new)), asns, tas)
    added, removed, changed = diff(old, new)

    if args.json:
        json.dump({
            "added": [v._asdict() for v in added],
            "removed": [v._asdict() for v in removed],
            "changed": [{"old": o._asdict(), "new": n._asdict()} for o, n in changed],
        }, sys.stdout, indent=2)
        print()
    else:
        for v in added:
            print(f"+ AS{v.asn:<10} {v.prefix:<24} max {v.max_length:<3} {v.ta}")
        for v in removed:
            print(f"- AS{v.asn:<10} {v.prefix:<24} max {v.max_length:<3} {v.ta}")
        for o, n in changed:
            print(f"~ AS{o.asn:<10} {o.prefix:<24} max {o.max_length} -> {n.max_length} {n.ta}")
        print(f"{len(added)} added, {len(removed)} removed, {len(changed)} changed", file=sys.stderr)

    return 1 if (added or removed or changed) else 0


if __name__ == "__main__":
    sys.exit(main())
