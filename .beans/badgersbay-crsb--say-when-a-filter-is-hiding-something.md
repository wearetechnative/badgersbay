---
# badgersbay-crsb
title: Say when a filter is hiding something
status: completed
type: task
priority: normal
created_at: 2026-09-17T14:29:48Z
updated_at: 2026-09-18T11:32:41Z
parent: badgersbay-qeqg
---

An empty table under an active filter looks exactly like an empty round, and
those mean opposite things - one is nobody matching the filter, the other is
nothing to do.

The view should name the active filter and how many assets it is hiding, with a
way back to the whole round. The same applies to a filter that matches
everything: it should be visible that one is set at all, or a shared link will
be read as the full picture.


## Summary of Changes

A notice above the table naming the active terms, the number shown of the
number listed, the number hidden, and a link back to the whole round.

It is shown when the filter hides nothing too, so a shared address with an
inert filter is not read as the full picture. An empty table under a filter says
"No assets match this filter" where an empty round says "No assets in scope for
this round" - identical situations on the page, opposite meanings.

The notice counts the table's rows, which include the manual and retired assets
the denominator leaves out. Two totals on one page have to be told apart, so the
notice says in words that its total is not the denominator above.
