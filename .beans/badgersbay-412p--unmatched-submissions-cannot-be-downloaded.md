---
# badgersbay-412p
title: Unmatched submissions cannot be downloaded
status: todo
type: bug
priority: normal
tags:
    - dashboard
    - evidence
created_at: 2026-09-17T14:39:08Z
updated_at: 2026-09-17T14:39:08Z
---

The `/evidence/` route resolves under `submissions/` only
(`honeybadger_server.py:3902`), and the round view renders unmatched records as
text with no link. So a submission that matched no asset cannot be downloaded at
all.

Found while naming downloads for their asset
(`name-every-download-for-its-asset`): an end-to-end test for the unmatched case
returned 404, which is how the gap surfaced.

## Why this is the wrong file to have out of reach

An unmatched submission is a machine that scanned and was credited to nobody.
The round view names two reasons - `no_serial`, meaning the client could not read
the hardware, and `serial_not_in_register`, meaning the register is behind - and
both are resolved by looking at what the machine actually sent. That is the one
thing you cannot do.

`report-storage` already carried a scenario for an unmatched download filename,
so the behaviour was believed to exist. It does not.

## Scope

- Serve records under `unmatched/<key>/<record>/` through the same route
- Link them from the round view, beside the reason
- The naming is already handled: `evidence_download_name()` names a record
  without an `asset_id` for its serial, or its hostname and username

## Worth deciding

Whether an unmatched record should be downloadable by a dashboard user at all.
It is evidence from a machine nobody has yet tied to an asset, and the dashboard
uses one shared password. The alternative - leaving it unreachable - is what
exists today, and it has not been a decision so much as an omission.
