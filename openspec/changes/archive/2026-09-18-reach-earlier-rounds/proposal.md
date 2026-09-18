# Make earlier scan rounds reachable

## Why

A round closes and becomes the thing you account for later: an auditor asks what
coverage was in 2026-03, not what it is today. The server keeps every round -
the period is derived from the submission timestamp and nothing is overwritten -
and the dashboard offers no way to look at one.

The data and the routing are already there. `do_GET` honours `?period=`, so
`/?view=round&period=2026-03` works today. What is missing is the affordance:
`_dashboard_shell()` renders the period as static text and the two tabs both
carry the current period along, so reaching an earlier round means knowing the
URL scheme and typing it.

This is also a regression. The dashboard these views replaced had a period
selector; it did not survive the move.

## What Changes

- A round selector in `_dashboard_shell()`, so it appears on both views and
  keeps the active tab when the round changes
- The rounds offered are those with submissions, plus the current round even
  when nobody has submitted to it yet
- Newest first
- A round with no submissions renders as an empty round rather than an error

## Impact

- Affected specs: `compliance-dashboard`
- Affected code: `honeybadger_server.py` - `_dashboard_shell()`, plus a pure
  function for the list of rounds

## Not changed

How a past round is scoped. That was the open question in the bean, and reading
the code answered it: `AssetRegister.in_scope()` takes the round's own window
and returns the rows whose validity window overlaps it, so a closed round is
already computed against the register as it was then. Measured against the live
register: 2026-03 puts ten assets in scope and 2026-09 thirteen, the difference
being three machines issued after March. Nothing to decide, and nothing to
build.
