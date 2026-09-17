---
# badgersbay-4lej
title: Keep the round's figures whole while filtering
status: todo
type: task
priority: high
created_at: 2026-09-17T14:29:48Z
updated_at: 2026-09-17T14:29:48Z
parent: badgersbay-qeqg
---

The acceptance criterion of the epic, separated out because it is the part that
can go quietly wrong.

`1 of 10 assets scanned`, the per-owner bars and the bucket counts are
statements about the round. They are computed from `compute_round_state()` and
must keep being computed from the unfiltered state, however the table is
narrowed.

The failure to avoid: a reader filters to outstanding, the headline recomputes
to `0 of 9`, and that figure is screenshotted into an audit file. A compliance
number that depends on what the reader was looking at is worse than no filter.

Needs a test that pins it: apply every filter in turn and assert the summary is
byte-identical each time.
