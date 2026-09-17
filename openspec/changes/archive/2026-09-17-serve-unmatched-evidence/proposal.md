# Serve the evidence behind an unmatched submission

## Why

The round view names two reasons a submission matched no asset. `no_serial`
says the client could not read the hardware. `serial_not_in_register` says the
register is behind. Both are answered the same way: by opening what the machine
actually sent and seeing which one it is.

That is the one thing the dashboard does not let anyone do. The `/evidence/`
route resolves under `submissions/` only, so nothing under `unmatched/` has a
URL, and the round view renders those rows as plain text with no link beside
them.

The file exists. It was stored deliberately - a submission is never discarded,
whatever it resolves to - and then put out of reach. `report-storage` already
carried a scenario for naming an unmatched download, written on the assumption
that one could happen, with a note recording that it could not.

## What Changes

- The evidence route serves the two trees the server writes: the serial-keyed
  one and the unmatched one
- The round view links each unmatched submission's reports and archive beside
  the reason it was filed under
- Links are derived from where a record was written, not from the register
  serial, which is how a record with no register entry gets a link at all
- The read-only period archive stays unserved through this route, and a path
  climbing out of a tree is still refused

## Impact

- Affected specs: `report-storage`, `asset-register`
- Affected code: `honeybadger_server.py` - the `/evidence/` handler, the round
  view's unmatched block and its report badges
- Existing three-segment links keep working and keep meaning the serial-keyed
  tree
- The legacy `/reports/` route is unchanged
