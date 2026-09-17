---
# badgersbay-rstb
title: /health is blind to the serial-keyed layout
status: todo
type: bug
priority: high
tags:
    - monitoring
created_at: 2026-09-17T11:24:43Z
updated_at: 2026-09-17T11:24:43Z
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
