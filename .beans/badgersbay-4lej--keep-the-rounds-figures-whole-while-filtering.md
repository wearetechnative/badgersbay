---
# badgersbay-4lej
title: Keep the round's figures whole while filtering
status: completed
type: task
priority: high
created_at: 2026-09-17T14:29:48Z
updated_at: 2026-09-18T11:32:50Z
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


## Summary of Changes

Held structurally rather than carefully. `compute_round_state()` is never told
about the filter, and `generate_round_view_html()` renders the headline, the
meter, the key counts, the per-owner bars and the alerts from the state it
returns. Only then does it call `filter_round_state()`, whose result reaches
`_round_table()` and nothing else. There is no point in the function where a
filter is in scope and a figure has not already been rendered.

Pinned by `test_the_figures_are_the_same_under_every_filter`: the whole
progress panel, 1690 characters of it, is captured unfiltered and asserted
identical under fourteen filters in turn - every state, two owners, two classes,
two searches and two combinations. Only the owner bars' hrefs and the marker on
the selected one are excluded, because those two are about the reader's view by
design; every number, including the meter widths, is compared.

`test_the_headline_counts_the_round_not_the_view` states the same thing in the
sentence people actually read.
