---
# badgersbay-u8tt
title: Report downloads have generic names
status: completed
type: bug
priority: normal
tags:
    - dashboard
    - evidence
created_at: 2026-09-17T14:31:31Z
updated_at: 2026-09-17T14:40:07Z
---

Downloading the evidence behind an asset gives:

    TARI-00023-2026-09-17-wouter.toorren.tar.gz    the archive
    lynis-report.json                              the report
    fastfetch-report.json                          the report

The archive carries the register's proof-file convention. The reports do not.
Download two assets' reports into one folder and the second overwrites the
first, or the browser appends `(1)` and you are left guessing which is which.

## Cause

`honeybadger_server.py:3818`:

    if record.is_file() and target.suffix == '.gz':

The naming is gated on `.gz`. Everything else falls through to
`download_name = target.name`, which is the name the file had inside the
archive - and that name is the same for every asset in the fleet.

The comment directly above says the intent plainly: *"Downloads carry the
register's proof-file convention, so the file can go straight into the audit
folder under the name the compliance sheet expects."* That is true of exactly
one of the three files on offer.

## Why it matters beyond tidiness

`proof_file` in the compliance workbook holds values like
`TARI-00023-2026-09-14`. The point of the convention is that a downloaded file
drops into the audit folder and is already named as the evidence for a
particular asset in a particular round. A file called `lynis-report.json` has to
be renamed by hand before it is evidence of anything, and a hand-renamed file is
one somebody has to be trusted about.

## Fix

Apply the same naming to every file the endpoint serves, with the report type
kept so the files remain distinguishable from one another:

    TARI-00023-2026-09-17-wouter.toorren.tar.gz
    TARI-00023-2026-09-17-wouter.toorren-lynis.json
    TARI-00023-2026-09-17-wouter.toorren-fastfetch.json

Worth deciding while in there: what an unmatched submission downloads as. It has
no `asset_id`, so it cannot follow the convention, and falling back to the
generic name is what produces the collision in the first place. The serial is
the identity it does have.


## Done

OpenSpec change `2026-09-17-name-every-download-for-its-asset`, archived.

`evidence_download_name()` builds the name from the served filename and the
submission record, and the handler uses it for every file rather than only for
`.gz`. The old shape - a default assignment, then an `if` that replaced it for
one suffix - is how the archive came to be the only file that followed the rule.

    TARI-00023-2026-09-17-wouter.toorren.tar.gz
    TARI-00023-2026-09-17-wouter.toorren-lynis.json
    TARI-00023-2026-09-17-wouter.toorren-fastfetch.json

`.tar.gz` is treated as one suffix; `Path().suffix` would call it `.gz` and
strand `.tar` in the stem.

## What the tests turned up

An end-to-end test for the unmatched case returned 404. The `/evidence/` route
resolves under `submissions/` only and the round view links unmatched records
nowhere, so a submission that matched no asset cannot be downloaded at all -
while `report-storage` carried a scenario describing its download filename, so
the behaviour was believed to exist.

The naming for that case is implemented and covered by doctests; the missing
route is `badgersbay-412p`. The spec scenario now states the rule without
claiming a user can reach it.

## Verification

26 tests and 59 doctests pass. The end-to-end tests assert on
`Content-Disposition` rather than on the function, so they would catch the
handler being wired to the wrong thing.
