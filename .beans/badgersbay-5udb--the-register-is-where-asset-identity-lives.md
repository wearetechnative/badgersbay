---
# badgersbay-5udb
title: The register is where asset identity lives
status: completed
type: task
priority: normal
tags:
    - register
    - iso
created_at: 2026-09-18T11:24:40Z
updated_at: 2026-09-18T11:27:31Z
---

OpenSpec change: `register-owns-asset-identity`.

The xlsx export out of the ISO tool was a one-off, used once to get the asset
list in order. The register in badgersbay is now the working list and the place
asset identities are maintained. Decided explicitly; this bean records the
specification consequence.

## What the spec says today

`openspec/specs/asset-register/spec.md` carries a requirement **"Where the
durable identity comes from"**: `asset_id` SHALL be the identifier the ISO tool
assigns, badgersbay SHALL NOT issue identifiers of its own, with a scenario
"The register is not the registrar" arguing that two issuers would drift.

That is the opposite of the decision, and it was already untrue in practice.
`TARI-00022` (`PF50L2ML`, Mathijs van Veluw) and `TARI-00041` (`MP1Y69AC`, Pim
Snel) were assigned by hand during the rebuild and exist only in this register
(recorded in `badgersbay-kgl2`). A specification that contradicts what is
actually done is worse than none, because it is read as the rule.

## What changes

Specification only. The requirement is REMOVED, with a reason and a migration
line, and replaced by an ADDED one saying that the register is the record of
asset identity: `asset_id` is assigned and maintained here, a number is never
reused once issued, and two rows may share an `asset_id` only as a serial
history of one asset over time. The two scenarios worth keeping travel with it:
identity follows the asset rather than its holder, and one asset may carry
several serials distinguished by validity windows. What the decision adds: how a
new asset gets a number, and that divergence from the ISO tool is expected
rather than a fault - it was a source used once, not a system this one syncs
with.

REMOVED plus ADDED rather than MODIFIED, deliberately: keeping the name over a
reversed meaning would hide that the old rule was wrong.

## What the loader actually validates

Worth stating so the new requirement does not imply enforcement that is not
there. `AssetRegister.load()` checks required columns, a non-empty `asset_id`, a
usable serial, `class` in `VALID_ASSET_CLASSES`, `status` in
`VALID_ASSET_STATUSES`, parseable dates, `valid_to` not preceding `valid_from`,
and - in `_check_serial_overlaps()` - that one serial never has overlapping
validity windows. Nothing checks `asset_id` at all beyond emptiness: not its
shape, not reuse of a retired number, not that rows sharing an `asset_id` form a
non-overlapping series. The requirement has to say so rather than imply a check.


## Closed

Archived as `openspec/changes/archive/2026-09-18-register-owns-asset-identity`.

What was verified, and how:

- No code change was needed. Read `AssetRegister` and its docstrings, and
  grepped the module for the old rule's wording (issuer, registrar, assigns,
  Asset tag). `honeybadger_server.py` never named the ISO tool as the source of
  `asset_id`; its remaining mentions of the tool concern deviations being
  justified there, which this decision does not touch.
- `python3 -m doctest honeybadger_server.py` - clean, before and after.
- `python3 -m unittest test_asset_inventory` - 41 tests, OK, before and after.
  Another session is mid-edit on `_round_table()` and `_dashboard_shell()` in
  the same tree; the baseline run was taken first so a failure could be told
  apart from this change. None appeared.
- `openspec validate register-owns-asset-identity --strict` and
  `openspec validate --specs --strict` (14 specs) - both pass, before and after
  the delta was synced into `openspec/specs/asset-register/spec.md`.

Two related statements were left standing on purpose. The Purpose of
`asset-register` and the "Load asset register" requirement still describe the
register as exported from the ISO reporting sheet. That is how the current file
was produced and it says nothing about who issues identities, so correcting it
would be rewriting history rather than a rule.

The one thing this change records but nothing enforces: `asset_id` reuse, and
two unrelated assets sharing a number, load without complaint. It is stated in
the requirement as an explicit non-guarantee rather than left to be assumed.
