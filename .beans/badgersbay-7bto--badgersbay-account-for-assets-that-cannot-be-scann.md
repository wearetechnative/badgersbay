---
# badgersbay-7bto
title: 'badgersbay: account for assets that cannot be scanned'
status: completed
type: feature
priority: high
tags:
    - badgersbay
    - iso27001
created_at: 2026-09-16T08:46:57Z
updated_at: 2026-09-16T08:46:57Z
---

An asset that cannot be scanned in a round is a deviation, justified in the ISO
tool. Badgersbay does not hold that justification - it records that one exists,
so the round can close instead of showing a permanently red row nobody can act
on.

## Summary of Changes

A control on each outstanding row records a reason and the operator's name, and
the asset moves to a third category. Progress reads
`scanned / accounted for / outstanding` rather than a single percentage.
Folding accounted-for into scanned would merge "we hold evidence" with "we hold
an excuse", and the deviation count is what the ISO tool needs as its own
figure.

Exceptions are keyed on asset and round and stored under
`reports/exceptions/<period>/<asset_id>.json`, beside the reports and for the
same reason: they are evidence, they survive a restart, and an auditor can be
handed them. An asset unreachable in September may be reachable in March, so
nothing carries over when the next round opens.

A submission always wins. If an accounted-for asset submits after all, the
submission counts and the exception lapses without anyone withdrawing it - the
alternative creates a state where evidence exists but is not counted.

The write path is one POST behind the dashboard's basic auth. That is a single
shared password, so the recorded name is what the operator typed and is
labelled self-reported wherever it appears.

Also: `--asset-register PATH` overrides the register named in the config file,
so a deployment can point at an agenix secret without editing the generated
config. The previously loaded register is remembered, and an asset that vanishes
from a later one is named on the dashboard - a filtered or truncated export
silently raises the coverage rate, which is the one direction a compliance
figure must never move by accident. The server still starts: taking the portal
down mid-round because two laptops were retired is worse than the risk. A
structurally invalid register does refuse startup.

Verified end to end: marking moves the count from outstanding to accounted for
and not to scanned; an empty reason returns 400 and an unauthenticated request
401; a submission for an accounted-for asset flips it back to scanned; nothing
carries into 2027-03; two exceptions survive a restart; a register short by two
assets starts and names them; an unknown platform class refuses startup.

Change archived as `2026-09-16-register-administration`.

## Follow-up

The elastinix side - the `assetRegisterFile` module option and its
documentation - is tracked as `elastinix-l16a`.
