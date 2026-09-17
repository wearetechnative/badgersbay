---
# badgersbay-qeqg
title: Filtering on the scan round view
status: todo
type: epic
priority: normal
tags:
    - dashboard
created_at: 2026-09-17T14:29:24Z
updated_at: 2026-09-17T14:29:24Z
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
