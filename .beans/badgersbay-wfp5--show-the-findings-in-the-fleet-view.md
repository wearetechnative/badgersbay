---
# badgersbay-wfp5
title: Show the findings in the fleet view
status: completed
type: task
priority: high
tags:
    - badgersbay
created_at: 2026-09-16T09:02:52Z
updated_at: 2026-09-16T09:17:47Z
parent: badgersbay-ucgi
---

Five columns: disk encryption, screen lock, firewall, hardening score, OS
up-to-date. These are the ones the dashboard mockup marked as phase 2.

A null value reads as unknown with the client's reason, not as blank - the
client declines to assert a value for vulnerable packages because the
spreadsheet contradicts itself about which one means compliant, and that
refusal is information.

An asset with no inventory reads as unknown rather than as a failure. Older
clients and Windows send none, and the asset did nothing wrong; colouring it
red teaches people to ignore the colour.

No colour judgement on the values. Whether a hardening score of 62 is
acceptable is a threshold that belongs to the ISO process. The client already
reports its own verdict in the finding text; the dashboard shows the number and
that text and adds nothing.

Tasks 3.1 to 3.5 in the OpenSpec change.


## Summary of Changes

Five columns in the fleet view, driven by the module-level `INVENTORY_COLUMNS` and rendered by `_inventory_cells()` / `inventory_cell()`, under a grouped header reading "Audit findings - as reported by the client".

Each value carries the finding it came from in a `title`, so provenance is on the row. A null value renders as `unknown` with the client's reason shown as a visible sub-line, not blank. An asset with no inventory, and one never seen at all, render as `unknown` in all five columns without changing the row's coverage state.

No finding cell uses a verdict class - `test_the_view_adds_no_verdict` asserts it. The legend says where the columns come from and what unknown means.
