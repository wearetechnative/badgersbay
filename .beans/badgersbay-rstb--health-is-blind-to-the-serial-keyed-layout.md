---
# badgersbay-rstb
title: /health is blind to the serial-keyed layout
status: completed
type: bug
priority: high
tags:
    - monitoring
created_at: 2026-09-17T11:24:43Z
updated_at: 2026-09-17T13:37:07Z
---

`get_health_status()` has two branches. In compliance mode it walks only
directories whose name passes `is_audit_period_dirname()`:

    if self.config.compliance_enabled:
        for period_dir in storage_path.iterdir():
            if not is_audit_period_dirname(period_dir.name):
                continue

`submissions/` is not such a directory, and neither is `unmatched/`. So the
counts `/health` reports come entirely from the pre-serial archive, and no
submission written under the layout the server actually uses today is counted.

## Why this is about to matter

Today `/health` reports 17 directories and 13 hosts, all of them from the
archive. `honeybadger-server` is otherwise fine, so nothing looks wrong.

The moment those directories are archived out of the round, `/health` will
report zero - and it will stay at zero as the fleet resubmits, because every
new submission goes to `submissions/<SERIAL>/`. An uptime monitor scraping this
endpoint sees a server that has stopped receiving anything, on a day when it is
receiving everything.

## Fix

Count the trees the server reads. `ComplianceCache._scan_submissions()` already
knows which three those are; health should agree with it rather than keep its
own idea of where submissions live. A record under `submissions/` counts, one
under `unmatched/` counts and is worth reporting separately, and the period
directories are archive.

Worth deciding while in there: `/health` is the one unauthenticated endpoint,
so whatever it reports is public to anyone who can reach the port. Counts are
fine; hostnames are already exposed through `unique_hosts` today.


## Done

OpenSpec change `2026-09-17-health-counts-what-the-server-reads`, archived.

`get_health_status()` now walks the same three trees
`ComplianceCache._scan_submissions()` reads, in one pass, with the mode branch
gone - the layout was never a property of the compliance flag. A submission
record counts as one, which is what a system directory meant before the layout
changed, so a monitor with a threshold on `total_report_directories` keeps
measuring the same thing.

`statistics.by_source` is new: `matched`, `unmatched`, `archived`. An unmatched
submission - a machine scanning without being credited to any asset - was
invisible in this endpoint and can now be alerted on.

Hostnames come from `submission.json` where the record has one. The old code
split directory names, which is the same fragile parsing that produced wrong
usernames in `honeybadger-cibm`.

## Spec

"Directory and host statistics" is REMOVED rather than modified. It described
two layouts selected by a flag and counted only the matching one; keeping the
name over different behaviour would have hidden that the old description was
wrong. Replaced by "Submission statistics".

## Verification

23 tests pass, five of them new. The regression test was mutation-checked: with
the serial-keyed tree removed from the walk, `test_a_real_submission_is_counted`
and `test_the_hostname_comes_from_the_record` both fail. There is also a test
that a tree holding only archive period directories is still counted, so the fix
does not trade one blind spot for another.
