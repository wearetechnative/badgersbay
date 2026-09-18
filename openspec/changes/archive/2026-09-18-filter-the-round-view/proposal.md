# Filter the scan round view

## Why

The round view groups assets into sections - scanned, accounted for,
outstanding, left scope without a reason, manual, retired - and offers no way
to narrow them. With thirteen assets that is inconvenient. It stops being
merely inconvenient the moment the register covers the whole fleet.

The questions the view cannot answer today are the ones people actually ask:
what does Pim still owe, which Linux machines are outstanding, where is
TARI-00031. Each of those currently means reading the whole page.

The per-owner bars in the progress panel already invite the click. A reader who
sees `Pim Snel 1/3` will try to press it, and nothing happens.

## What Changes

- Narrow the round table by state, by owner and by platform class
- Find one asset by its id or its hardware serial
- The round's figures - the headline, the meter, the per-owner bars and the
  bucket counts - keep describing the round, not the view
- Say when a filter is active, how many assets it hides, and offer the way back
- The per-owner bars become links to that owner's filtered view
- Changing the round keeps the filter, so `period=` and the filter compose

## Impact

- Affected specs: `compliance-dashboard`
- Affected code: `honeybadger_server.py` - new pure functions for parsing,
  matching and narrowing; `generate_round_view_html()`, `_round_table()`,
  `_dashboard_shell()`, `do_GET`, and the dashboard stylesheet

## Not changed

The fleet view. It has its own shape and its own columns, and whether it gets
the same control is a separate question.

The bucket computation. `compute_round_state()` is not given the filter and
does not learn about it: the narrowing happens between the state and the table,
which is the structural reason the figures cannot drift.
