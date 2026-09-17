---
# badgersbay-d2x1
title: Archive the pre-serial submissions out of the live round
status: in-progress
type: task
priority: normal
tags:
    - operations
created_at: 2026-09-17T11:24:43Z
updated_at: 2026-09-17T11:24:43Z
---

The round view counts 17 systems that were scanned but cannot be matched,
because they were submitted before storage was keyed on the hardware serial.
They are read as archive records without a serial, so every one of them lands
as unmatched and the coverage figure for the running round is wrong in the one
direction a compliance figure must not be wrong: it understates.

The plan is to archive them and have the systems submit once more, so the round
is measured against real, matchable submissions.

## What is on disk

    /data/badgersbay/reports/          3.0M
      2026-03/                         9 system directories   pre-serial
      2026-09/                         8 system directories   pre-serial
      submissions/PF50L2MR/            1                      serial-keyed
      register-previous.json

## Why moving them is enough

`ComplianceCache._scan_submissions()` reads three trees: `submissions/`,
`unmatched/`, and any directory whose name passes
`is_audit_period_dirname()` - which is `len(name) == 7 and name[4] == '-'`.

So a directory named anything other than `YYYY-MM` is invisible to the server.
Moving `2026-03` and `2026-09` under `archive-pre-serial/` keeps every byte in
place and takes them out of every view, with no code change and nothing
deleted.

That the period directories are read at all was deliberate - the docstring says
"so that switching layout does not empty a round that is already running". That
was the right call during the switch. It is the wrong one now: the round it
keeps alive is made of records that can never match the register.

## What this costs

Once archived, nothing in the product can show them. If an auditor later asks
what coverage was in 2026-03, these are the records that answer it and they
will not be reachable from the dashboard. `badgersbay-btmz` - making earlier
rounds reachable - would have to account for this tree if that ever matters.

Accepted deliberately: the systems are being asked to resubmit, so the round
will be rebuilt from submissions that carry a serial.

## Steps

- [ ] Record the byte count and directory count before
- [ ] `mkdir -p /data/badgersbay/reports/archive-pre-serial`
- [ ] `mv 2026-03 2026-09` into it
- [ ] Confirm the same byte count and directory count afterwards
- [ ] Restart badgersbay - the cache is built at startup, so it will keep
      serving the old round until it is
- [ ] Ask the fleet to submit once more
