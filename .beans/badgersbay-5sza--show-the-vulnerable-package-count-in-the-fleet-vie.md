---
# badgersbay-5sza
title: Show the vulnerable package count in the fleet view
status: completed
type: feature
priority: normal
tags:
    - dashboard
    - inventory
created_at: 2026-09-16T12:33:56Z
updated_at: 2026-09-16T12:38:26Z
---

honeybadger `23f7d8e` (bean `honeybadger-rn0a`) added a `count` to the
`vulnerable_packages` finding and raised `asset-inventory.json` to
`schema_version` 2. badgersbay is still written against 1 and shows no column
for the field, so the number arrives, is stored in `submission.json`, and is
seen by nobody.

That leaves `rn0a` half done. Its complaint was that the count survived only in
Dutch prose where nothing could read it; storing it in a record nobody renders
moves the problem rather than solving it.

## Two halves, and why the second is not optional

`INVENTORY_SCHEMA_VERSION` is 1, so every submission from the new client logs:

    Asset inventory schema_version 2 is not 1; stored whole and read for the
    fields this server understands

Bumping the constant alone would silence that. But the comment above it says
"the schema generation this server was written against", and schema 2 adds
exactly one thing: the count. Claiming to be written against 2 while ignoring
the only thing 2 adds makes the constant untrue, and that log line is precisely
the signal that fields are arriving which nothing renders. So the bump and the
column go together or neither does.

## Why `value` stays null

The client deliberately asserts no value for this finding: the asset register
contradicts itself about which literal in column J means compliant - its data
validation says `None`, its Status formula counts `Yes`. honeybadger refuses to
pick one and says why in the finding text. The count is a measurement; the
verdict is not honeybadger's to give.

badgersbay must not invent that verdict either. The column shows the number and
the client's reason, and applies no colour - the same rule the other inventory
columns already follow.

## Scope

- `INVENTORY_SCHEMA_VERSION` 1 -> 2
- `vulnerable_packages` added to `INVENTORY_COLUMNS`
- `inventory_cell()` falls back to `count` when `value` is null, so a
  deliberately undecided finding can still report a measurement

`inventory_cell()` is shared by every column, so its doctests change with it.

## Checked, not assumed

- `parse_asset_inventory()` does not inspect the version and does `dict(finding)`,
  so `count` already survives into the record and into `inventory_raw`
- schema 2 is additive only: one extra key through the existing `extra_key`
  mechanism in `_inventory_finding`
- `test_asset_inventory.py` already pins that an unknown generation is stored
  and rendered, so the bump cannot regress that behaviour silently


## Done

Implemented on `consume-asset-inventory`. OpenSpec change
`2026-09-16-show-vulnerable-package-count` archived, `compliance-dashboard`
spec synced, CHANGELOG updated.

- `INVENTORY_SCHEMA_VERSION` 1 -> 2
- `vulnerable_packages` is the sixth entry in `INVENTORY_COLUMNS`, labelled
  **Vulnerable pkgs**
- `inventory_cell()` reports a finding's `count` when its `value` is null

The fallback is stated generally rather than as a branch for this one field, so
the next finding that measures without judging needs no new case. `bool` is
excluded explicitly - it is an `int` in Python, and `True` rendering as `1` in a
count column would be a measurement nobody made.

## Verification

18 tests in `test_asset_inventory`, all doctests, and `openspec validate
--specs --strict` (14 items) pass.

The new end-to-end test was mutation-checked rather than merely observed to
pass: with the `count` fallback removed it fails on the rendered row, which
reads `unknown` with the reason where the number should be. Both new tests
assert against the column's own cell rather than anywhere on the row - an
unqualified search would have passed on any other column reading unknown.

## One test corrected while here

`test_findings_reach_the_record` asserted
`inventory['schema_version'] == hb.INVENTORY_SCHEMA_VERSION` against a captured
real archive. That passes by definition and hides the case it exists for: the
client runs ahead of the server, so a real submission is routinely a generation
the server was not written against. It now asserts the archive's own generation,
1, with the reasoning recorded beside it.
