---
# badgersbay-1ya5
title: Narrow the round table by state
status: completed
type: task
priority: normal
created_at: 2026-09-17T14:29:48Z
updated_at: 2026-09-18T11:32:26Z
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


## Summary of Changes

`state=` on the round view, one of `scanned`, `accounted`, `outstanding`,
`unexplained`, `manual` or `retired`. It selects whole sections where the
sections are assembled - `filter_round_state()` between `compute_round_state()`
and `_round_table()` - and nowhere else.

`accounted` covers both buckets that resolve an asset without evidence, a
recorded exception and a departure with a reason, because they read as one
section in the table and one segment in the meter. They stay apart in the data.

A value outside the vocabulary is dropped rather than honoured, and the view
says so: an empty page is the worst answer to a typo in an address, because it
reads exactly like a finished round.
