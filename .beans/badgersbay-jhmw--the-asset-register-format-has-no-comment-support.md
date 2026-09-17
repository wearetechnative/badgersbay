---
# badgersbay-jhmw
title: The asset register format has no comment support
status: todo
type: bug
priority: low
tags:
    - register
created_at: 2026-09-17T13:13:28Z
updated_at: 2026-09-17T13:13:28Z
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
