# Count what the server actually reads in /health

## Why

`/health` reports zero submissions on a server that is receiving them.

The endpoint walks one of two layouts chosen by whether compliance mode is on.
In compliance mode it iterates only directories whose name passes
`is_audit_period_dirname()`. `submissions/` is not such a directory and neither
is `unmatched/`, so nothing written under the layout the server has used since
submissions became keyed on the hardware serial is counted at all.

Until today the numbers looked plausible because the pre-serial archive was
still in place and supplied them. That archive has been moved aside, so the
endpoint now reports `0` directories and `0` hosts while the fleet submits.

`/health` is the one unauthenticated endpoint and therefore the one a monitor
scrapes. A monitor watching this sees a server that has stopped receiving
anything on the day it receives everything - and, worse, it would have kept
reporting a healthy number while the real storage tree sat empty.

## What Changes

- `get_health_status()` counts the three trees `ComplianceCache._scan_submissions()`
  reads: `submissions/`, `unmatched/`, and the period directories kept as archive
- A submission record counts as one directory, which is what a system directory
  meant before the layout changed
- `statistics.by_source` is added, breaking the total down into matched,
  unmatched and archived - an unmatched submission is a real signal and is
  currently invisible
- The existing keys keep their names and meaning, so a monitor reading them does
  not break

## Impact

- Affected specs: `health-monitoring`
- Affected code: `honeybadger_server.py` - `get_health_status()`
