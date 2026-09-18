---
# badgersbay-btmz
title: Make earlier scan rounds reachable from the dashboard
status: completed
type: feature
priority: normal
tags:
    - dashboard
created_at: 2026-09-17T10:18:58Z
updated_at: 2026-09-18T08:54:27Z
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


## Done

OpenSpec change `2026-09-18-reach-earlier-rounds`, archived.

A round selector in `_dashboard_shell()`, so it appears on both views. It offers
the rounds that have submissions plus the round being viewed, newest first, and
carries the active tab so changing the round keeps you on the view you were
reading.

`selectable_rounds()` is a pure function with doctests. The addition of the
current round is the part that matters: the list of rounds with data comes from
the submissions, so a round nobody has submitted to yet is not in it - and that
is exactly the round you are looking at when one opens.

## A form, not a script

The previous dashboard navigated by `onchange`, and its filter needed fixing in
two separate changes. This is a plain GET form: it works with scripting off, the
address survives a reload and can be sent to someone, and it is testable by
reading HTML rather than by driving a browser. The cost is one small button.

## The open question answered itself

The bean asked whether a closed round should render the register as it was then
or as it is now, and warned that getting it wrong rewrites a historical figure.
Reading the code settled it: `in_scope()` takes the round's own window, so a
past round is already computed against the register as it was.

Measured against the live register: 2026-03 puts ten assets in scope and 2026-09
thirteen, the three extra being machines issued after March. No code was needed.

A test pins it anyway, because a regression there would be silent. It builds its
own register rather than using the harness one, whose rows are all valid from
2024 - against those, any assertion about scoping passes by construction and
proves nothing. The test now asserts that an asset issued in August is absent
from March, and that one that left in May is still counted in the round it
belonged to.

## Verification

41 tests and 63 doctests, `openspec validate --specs --strict` 14 of 14.

The selector tests were mutation-checked: removing the control from the shell
fails three of them.
