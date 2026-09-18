---
# badgersbay-qeqg
title: Filtering on the scan round view
status: completed
type: epic
priority: normal
tags:
    - dashboard
created_at: 2026-09-17T14:29:24Z
updated_at: 2026-09-18T11:32:59Z
---

The scan round view groups assets into sections - scanned, accounted for,
outstanding, left scope without a reason, manual - and offers no way to narrow
them. With thirteen assets that is merely inconvenient. It stops being
inconvenient the moment the register covers the whole fleet, which is where it
is heading.

The questions the view cannot answer today are the ones people actually ask:
what does Pim still owe, which Linux machines are outstanding, where is
TARI-00031. Each of those currently means reading the whole page.

## The constraint that makes this worth an epic

A filter must never change the round's figures.

`1 of 10 assets scanned` is a compliance statement about the round. If
filtering to "outstanding" also changed that headline to `0 of 9`, the number
on the page would depend on what the reader happened to be looking at - and
somebody would eventually screenshot it for an audit. The progress panel, the
per-owner bars and the bucket counts all describe the round, not the view, and
they stay put while the table narrows.

This is the whole reason the work needs stating rather than just doing.

## A filter should be shareable

The obvious implementation is client-side JavaScript, which is what the legacy
dashboard used and what broke twice (its `Show` filter needed fixing in two
separate changes). A query parameter costs no more, survives a reload, and can
be pasted into a message to the person who owes a scan - which is the main
thing anyone would do with a filter here.

It also composes with `period=`, which the view already honours, so a filtered
view of a closed round is a link rather than a sequence of clicks.

## Scope

- Narrow by state, by owner, and by platform class
- Find one asset by id or serial without reading the page
- The round's figures stay whole under every filter
- Say when a filter is active and what it hides, so an empty table is never
  mistaken for an empty round

## Not in scope

The fleet view has its own shape and its own columns; whether it gets the same
control is a separate question. Making earlier rounds reachable is
`badgersbay-btmz`, and the two should agree on how the URL is spelled if both
land.


## Summary of Changes

The round view's table narrows by `state=`, `owner=`, `class=` and `q=`, all
query parameters on `/?view=round&period=<round>`, composing with each other and
with the round selector, which carries them so changing the round keeps the
question.

The constraint held. The figures are rendered before the filtered copy exists,
which is why a filter cannot reach a compliance number - see badgersbay-4lej for
how it is pinned.

Children: badgersbay-4lej, badgersbay-1ya5, badgersbay-guxx, badgersbay-u45r,
badgersbay-crsb, all completed.

New pure functions, all doctested and unaware of the handler: `search_key()`,
`parse_round_filters()`, `round_filter_terms()`, `round_view_href()`,
`round_row_entry()`, `round_row_matches()`, `filter_round_state()`.

OpenSpec: `2026-09-18-filter-the-round-view`, archived. Four requirements added
to `compliance-dashboard`.

Verified: 116 doctests, 66 unit and end-to-end tests (25 of them new),
`openspec validate --all --strict`, `nix flake check`.

Not done, and deliberately: the fleet view has its own shape and its own
columns, and whether it gets the same control is a separate question.
