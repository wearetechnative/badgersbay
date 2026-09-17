---
# badgersbay-1ya5
title: Narrow the round table by state
status: todo
type: task
priority: normal
created_at: 2026-09-17T14:29:48Z
updated_at: 2026-09-17T14:29:48Z
parent: badgersbay-qeqg
---

A control that shows only one of the sections the table already builds:
scanned, accounted for, outstanding, left scope without a reason, manual.

Outstanding is the one people will use. It is the list of who still has to act,
and today you get it by scrolling past everyone who already did.

As a query parameter rather than a script, so the link survives a reload and can
be sent to someone. It composes with `period=`, which the view already honours.

The sections are built in `_round_table()` from the buckets `compute_round_state()`
returns, so the narrowing happens where the groups are assembled and nowhere
else.
