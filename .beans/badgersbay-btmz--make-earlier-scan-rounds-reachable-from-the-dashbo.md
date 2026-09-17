---
# badgersbay-btmz
title: Make earlier scan rounds reachable from the dashboard
status: todo
type: feature
priority: normal
tags:
    - dashboard
created_at: 2026-09-17T10:18:58Z
updated_at: 2026-09-17T10:18:58Z
---

A round closes and becomes the thing you have to account for later: the ISO
auditor asks what coverage was in 2026-03, not what it is today. The server
keeps every round - `get_audit_period()` derives the period from the submission
timestamp and nothing is overwritten - but the dashboard gives you no way to
look at one.

## What is actually missing

The data and the routing are already there. `do_GET` honours `?period=`, and
both views take the period as an argument, so this URL works today:

    /?view=round&period=2026-03

What is missing is the affordance. `_dashboard_shell()` renders the period as
static text:

    <div class="ctx">Audit round <strong class="mono">2026-09</strong> ...

and the only navigation it offers is the two tabs, which both carry the current
period along. So the only way to reach an earlier round is to know the URL
scheme and type it.

## This is a regression against the view it replaced

The legacy dashboard had a period selector - `generate_compliance_dashboard_html()`
takes `selected_period`, and its JavaScript still reads:

    window.location.href = '/?period=' + period;

That control did not survive the move to the round and fleet views. Someone who
used the old dashboard will look for it and not find it.

## The list of rounds is already computed

`generate_fleet_view_html()` does this to find the preceding round:

    periods = sorted({s['audit_period'] for s in self.compliance_cache.submissions})
    older = [p for p in periods if p < period]

So the set of rounds that have data is known. A selector needs that list, plus
the current round even when it has no submissions yet - otherwise the round you
are looking at disappears from its own selector the moment it is empty, which
is exactly when you are most likely to be looking at it.

## Scope

- A period control in `_dashboard_shell()`, so it appears on both views and
  keeps the active tab when it changes
- Offer the rounds that have data, plus the current one
- Order newest first; the current round is the common case
- A period with no submissions renders as an empty round, not an error - a
  round in which nobody scanned is a real answer and the register still says
  who should have

## Worth deciding, not assuming

Whether a closed round should render the register as it was *then* or as it is
now. A row retired since is still part of that round's denominator, and
`valid_from`/`valid_to` already carry the information to answer this. Getting it
wrong changes a historical compliance figure after the fact, which is the one
thing an audit trail must not do. `AssetRegister.in_scope()` and `retired()`
exist; check what they do for a past period before building the control.
