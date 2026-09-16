# Show the vulnerable package count in the fleet view

## Why

The honeybadger client now reports how many vulnerable packages an audit found.
`asset-inventory.json` rose to `schema_version` 2 to carry it, and badgersbay is
written against 1: the number arrives, is stored in `submission.json`, and is
rendered nowhere.

The client bean this came from (`honeybadger-rn0a`) existed because the count
survived only inside a Dutch sentence where nothing could read it. Storing it in
a record no view renders moves that problem rather than ending it.

There is a second reason not to stop at the storage layer. Every submission from
the new client logs:

    Asset inventory schema_version 2 is not 1; stored whole and read for the
    fields this server understands

Bumping the constant silences that line. But the constant means "the schema
generation this server was written against", and schema 2 adds exactly one
thing: this count. Bumping while ignoring it would make the constant untrue and
remove the only signal that unrendered fields are arriving. The bump and the
column belong to the same change.

## What Changes

- `INVENTORY_SCHEMA_VERSION` moves from 1 to 2
- `vulnerable_packages` joins `INVENTORY_COLUMNS` in the fleet view
- `inventory_cell()` reports a finding's `count` when its `value` is null, so a
  finding that deliberately asserts no verdict can still report a measurement

## Impact

- Affected specs: `compliance-dashboard`
- Affected code: `honeybadger_server.py` - `INVENTORY_SCHEMA_VERSION`,
  `INVENTORY_COLUMNS`, `inventory_cell()`
- No storage change. `parse_asset_inventory()` already keeps every key of every
  finding, so the count is present in records written before this change.
