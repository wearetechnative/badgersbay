---
# badgersbay-guxx
title: Narrow by owner and by platform class
status: completed
type: task
priority: normal
created_at: 2026-09-17T14:29:48Z
updated_at: 2026-09-18T11:32:30Z
parent: badgersbay-qeqg
---

Two questions the round view cannot answer: what does one person still owe, and
which machines of one platform are outstanding.

Owner matters because the per-owner bars already exist in the progress panel and
already invite the click - a reader who sees `Pim Snel 1/3` will try to press it.

Class matters for a different reason: Windows sits outside the denominator until
its client can submit, so "show me the Linux machines" is how somebody checks
the part of the fleet that is actually measurable right now.

Owner names come from the register and are free text, so the filter matches on
the value in the register rather than on a slug - `owner_to_slug()` exists for
naming proof files, not for identity.


## Summary of Changes

`owner=` and `class=` on the round view.

Owner matches the value the register holds, ignoring case, not a slug -
`owner_to_slug()` is lossy about name infixes and two owners can share one, so
it is a filename convention rather than an identity. A row with no owner answers
to `unassigned`, the word the progress panel already uses for that case.

The per-owner bars became links to that owner's view, carrying the other active
terms, and the bar for the owner being shown is marked. They already looked
pressable.

Class matters because Windows sits outside the denominator until its client can
submit, so a class filter is how somebody reads the part of the fleet that is
measurable now.
