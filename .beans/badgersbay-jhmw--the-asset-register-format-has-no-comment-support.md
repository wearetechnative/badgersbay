---
# badgersbay-jhmw
title: The asset register format has no comment support
status: completed
type: bug
priority: normal
tags:
    - register
created_at: 2026-09-17T13:13:28Z
updated_at: 2026-09-18T13:15:01Z
---

`AssetRegister.load()` hands the file straight to `csv.DictReader`, so the first
line is the header whatever it contains. A `#` comment at the top produces:

    assets.csv is missing required column(s): asset_id, class, owner, serial

which names the columns rather than the comment, so the reader looks for a
column problem that is not there. A comment further down parses as a data row
and fails validation on whatever field it lands in.

Found while rewriting `assets.csv.example`, where explaining the rows in place
was the obvious thing to do and broke the file.

## Why this is worth a line

The register is hand-maintained and delivered as an encrypted secret. Whoever
edits it cannot see the file in a diff or a review, and the one affordance every
hand-maintained config has - a note to the next person - refuses to start the
service. "Why is this row here" and "do not fix this serial, it is wrong
upstream" are exactly the things that should be written beside the row.

## Fix

Skip lines whose first non-whitespace character is `#` before handing the file
to `csv.DictReader`, and say so where the format is documented. A serial or an
owner name never legitimately starts with `#`.

Either way the error message deserves attention: when the header is unusable,
say what the first line was instead of listing the columns that were expected.


## Summary of Changes

`register_lines()` numbers the register's lines and drops the ones whose first
non-whitespace character is `#`; `load()` feeds `csv.DictReader` that generator
instead of the file handle. A note may sit above the header and between rows.

The line numbers travel with the text, so `assets.csv row 6` still means line 6
of the file the maintainer opens, notes counted. Without that, every note would
shift the errors after it one line further out, and commenting would be punished
with a wrong error rather than a refusal - which is worse. It also fixes the
same drift from a blank line or an embedded newline, which was there already.

The header error now reads `assets.csv line 2 is not a usable header: missing
required column(s): asset_id, class, owner, serial. The line reads: '...'` -
the columns that were wanted plus the line that arrived, quoted with `repr()`
so a stray BOM or tab is visible. An empty file, or one holding only notes,
says it has no header line instead of listing every column as missing. Same
shape as before: `AssetRegisterError`, raised from `load()`, refusing startup.

`assets.csv.example` now carries the notes it was written to have - why the
serial that disagrees with the ISO tool must not be "corrected", why a class
sits outside the denominator, how one asset holds two serials across a
mainboard replacement - and the README's register section documents the format.

Not done, deliberately: no comment preservation on write (the register is
read-only to the server, so there is no write path to preserve them through),
and nothing is parsed out of a comment. A fact the service acts on belongs in a
column, where it is validated.

OpenSpec: `2026-09-18-notes-in-the-asset-register`, archived. One requirement
added to `asset-register` ("A note may sit beside a row") and "Load asset
register" modified to require the header error to name and quote the line.

Verified: 116 doctests (4 new in `register_lines()`), 74 unit and end-to-end
tests, 8 of them new in `TestNotesInTheRegister` - a note above the header, a
note between rows that does not become a row, an indented note, a `#` inside a
field that is not a note, a row error naming line 6 in a register with three
notes, the header error quoting a semicolon-separated export, a register of
only notes, and `assets.csv.example` itself loading. `openspec validate --all
--strict`.

Mutation-checked: with the two skip lines removed from `register_lines()`,
`test_a_note_above_the_header` fails with the exact error from this bean
(`missing required column(s): asset_id, class, owner, serial`), and three other
tests fail with it. Restored, all 74 pass.
