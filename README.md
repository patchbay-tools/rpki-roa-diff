# rpki-roa-diff

Diff two RPKI ROA exports and see what changed: new VRPs, withdrawn VRPs, and VRPs whose
maxLength moved. Useful for keeping an eye on your own ROAs (or a customer's) between
validator runs, or for spotting a trust anchor that suddenly lost half its objects.

Reads the JSON format that both Routinator and rpki-client write:

```
routinator vrps -f json > today.json
rpki-client -j -d /var/cache/rpki-client /var/db/rpki-client   # writes json
```

Python 3.10+, standard library only.

## Usage

```
./roa_diff.py examples/old.json examples/new.json
```

```
+ AS64504      203.0.113.0/24           max 24  apnic
- AS64503      203.0.113.0/24           max 24  apnic
~ AS64501      198.51.100.0/22          max 22 -> 24 ripe
1 added, 1 removed, 1 changed
```

Filter to what you care about, or get JSON for another tool:

```
./roa_diff.py --asn AS64501 --ta ripe yesterday.json today.json
./roa_diff.py --json yesterday.json today.json | jq '.changed'
```

The exit status is 0 when nothing changed and 1 when something did, so it drops into a cron job:

```
./roa_diff.py --asn AS64500 last.json now.json || mail-the-noc
```

## Tests

```
python3 -m unittest discover -s tests
```
