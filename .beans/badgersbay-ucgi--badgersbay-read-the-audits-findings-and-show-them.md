---
# badgersbay-ucgi
title: 'badgersbay: read the audit''s findings and show them in the fleet view'
status: completed
type: epic
priority: high
tags:
    - badgersbay
    - iso27001
created_at: 2026-09-16T09:02:28Z
updated_at: 2026-09-16T09:19:15Z
---

Close the loop the exploration set out to close: the client determines the
compliance values, the server shows them, and nobody retypes them into the
spreadsheet.

## OpenSpec

Delivered through the existing change:

    openspec/changes/consume-asset-inventory/

Proposal, design, tasks and three capability deltas. Do not create it again -
implement, test, archive.

## Why this is open at all

The client has shipped `asset-inventory.json` since honeybadger 946337c. The
server stores the file inside the archive and reads nothing from it.

Three proposals deferred this piece and each pointed at the next:
`asset-register-identity` as a non-goal, `emit-asset-inventory-json` as
"badgersbay does not read this file yet", and the dashboard mockup as a column
group marked "phase 2". The last pointed nowhere, so the server side never got
an owner.

## Live consequence

`asset-inventory.json` is a JSON member, so it reaches the report type
detection, which does not know it:

    fastfetch.json          -> fastfetch
    lynis-report.json       -> lynis
    asset-inventory.json    -> None      unrecognised -> HTTP 207

Every submission from a current client answers 207 with an unrecognised member.
Nothing breaks - the archive is stored and the reports are processed - but every
submission reports that something needs attention when nothing does. Recognising
the file fixes that as a side effect.

## Acceptance criteria

1. A submission from a current client answers 200, with no unrecognised member.
2. The fleet view shows disk encryption, screen lock, firewall, hardening score
   and OS up-to-date for an asset whose latest submission carries an inventory.
3. A value the client declined to assert reads as unknown with the client's
   reason, not as blank.
4. An asset with no inventory - an older client, or Windows - reads as unknown
   rather than as a failure.
5. Completeness is unchanged by the presence or absence of an inventory. An
   older client does not become incomplete for a reason its owner cannot act on.
6. An inventory whose `schema_version` the server does not recognise is stored
   and rendered for the fields it does understand.
7. Malformed JSON is logged and skipped; the submission is stored regardless.
8. The whole document is kept, so fields not modelled today are not discarded.

## Done when

Every criterion is demonstrably met against a real archive from the current
client, the tests pass, and the OpenSpec change is archived.

## Out of scope

Writing the spreadsheet, and judging the values. Whether a hardening score of
62 is acceptable is a threshold that belongs to the ISO process; the dashboard
reports what was found and adds no verdict of its own.


## Summary of Changes

The client determines the compliance values, the server now reads them, and the fleet view shows them.

**Recognition.** `asset-inventory.json` is recognised by filename in `extract_and_validate_tar()` and carried out as `extraction['inventory']`, separate from `reports`. `detect_report_type_from_filename()` returns None for it explicitly. It never reaches the requirement set, so completeness is untouched by its presence or absence.

**The record.** `submission.json` gains `inventory` (parsed findings) and `inventory_raw` (the document whole). The document is also written into the record directory, which makes it downloadable through the existing `/evidence/` route.

**The view.** Five columns - disk encryption, screen lock, firewall, hardening score, OS current - under a grouped header. Each value carries its finding in a title; a declined value reads unknown with the reason shown; an asset with no inventory reads unknown, not as a failure. No cell is coloured as a pass or a failure.

All eight acceptance criteria are covered by tests in `test_asset_inventory.py`, run against a real archive from the current client. The 207 regression is verified to reproduce on the pre-change code.

OpenSpec change `consume-asset-inventory` archived as `2026-09-16-consume-asset-inventory`; its three capability deltas synced into `openspec/specs/`.
