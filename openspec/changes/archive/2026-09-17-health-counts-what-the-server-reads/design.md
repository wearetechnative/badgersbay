# Design

## One walk, not one per mode

The endpoint branched on `compliance_enabled` and walked a different tree in
each branch. That made the storage layout a property of a configuration flag,
which it never was: the server writes serial-keyed records whether or not
compliance tracking is on, and period directories exist only as history.

The walk now mirrors `ComplianceCache._scan_submissions()`, which is the
function that decides what the server considers a submission. Those two
disagreeing is what produced a report of zero.

## What counts as one

Before the layout changed, one directory was one system's submission on one
date, and `total_report_directories` counted those. The serial-keyed layout
keeps the same granularity one level deeper - `submissions/<serial>/<stamp>/` -
so a record counts as one and the number keeps its old meaning.

Counting serials instead would have been defensible but changes what the
existing key reports, and a monitor with a threshold on it would silently start
measuring something else.

## Unmatched is reported, not hidden

A submission that cannot be matched to the register is the interesting failure:
a machine is scanning and nobody is being credited for it. It was invisible in
this endpoint. `by_source` now separates matched, unmatched and archived, so the
number can be alerted on without opening the dashboard.

## Hostnames come from the record where there is one

A serial-keyed record carries its hostname in `submission.json`. The old code
derived a hostname by splitting a directory name, which is the same fragile
parsing that produced wrong usernames elsewhere. The name is read from the
record when it is there and parsed only for the archive, where no record file
exists.

## What stays out

No authentication change. `/health` remains unauthenticated, so what it reports
is public to anyone who can reach the port. Counts are fine; `unique_hosts`
already exposed the existence of hostnames and that is unchanged.
