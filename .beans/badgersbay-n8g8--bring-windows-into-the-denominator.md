---
# badgersbay-n8g8
title: Bring Windows into the denominator
status: todo
type: task
priority: normal
tags:
    - dashboard
    - register
created_at: 2026-09-18T09:14:17Z
updated_at: 2026-09-18T09:14:17Z
---

`MANUAL_CLASSES = {'windows'}` (`honeybadger_server.py`) keeps every Windows
asset out of the round's denominator, shown as `manual` with the text *client
cannot submit yet*. Three of eleven people are in that bucket: Elma Aker
(TARI-00031), Linda de Ridder (TARI-00029) and Richard van Os (TARI-00034).

That exception was right when it was written. The Windows client could not
bundle or submit anything, and a permanently red row for a reason its owner
cannot act on is the fastest way to teach people to ignore a dashboard.

## Blocked on, and this is not a formality

**honeybadger-dtrv** - verify the Windows audit end-to-end on a real Windows
machine. `honeybadger-k80g` is delivered and its seven build tasks are done, but
they were tested under pwsh against fixtures. Until a real machine has submitted
and been matched, "the client can submit" is a claim rather than an observation.

Removing the exception before that lands moves three people into the denominator
with a client that may not work, and the coverage figure drops for a reason
nobody can fix. That is worse than the exception it replaces.

## What the first Windows submission also settles

Two register values currently rest on a single reading each:

- `TARI-00031` carries `YD063JGA`, read once from `Win32_BIOS` on Elma's laptop.
  The ISO tool still holds `AC06CMEP`, which is the suffix of her Windows
  hostname.
- `TARI-00034` carries `PF-4VBTLB` with the hyphen the ISO tool writes. At
  Wouter's machine that hyphen proved to be decoration - the tool says
  `PF-50L2MR`, the machine reports `PF50L2MR` - and `normalise_serial()` does not
  strip separators, so a mismatch here would simply not match.

So the first real Windows submission is both the verification and the answer to
those two. If either lands as `serial_not_in_register`, the register is wrong
rather than the client.

## Steps

- [ ] Wait for `honeybadger-dtrv`
- [ ] Confirm the submission matched its asset rather than landing unmatched
- [ ] Remove `windows` from `MANUAL_CLASSES`, with the tests that cover the
      manual bucket updated rather than deleted - the bucket itself stays, for
      whatever needs it next
- [ ] Deploy, and expect the denominator to go from ten to thirteen
