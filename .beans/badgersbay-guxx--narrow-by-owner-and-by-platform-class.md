---
# badgersbay-guxx
title: Narrow by owner and by platform class
status: todo
type: task
priority: normal
created_at: 2026-09-17T14:29:48Z
updated_at: 2026-09-17T14:29:48Z
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
