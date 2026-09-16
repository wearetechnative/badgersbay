---
# badgersbay-sqnk
title: Tests and verification against a real archive
status: todo
type: task
priority: normal
tags:
    - badgersbay
created_at: 2026-09-16T09:02:52Z
updated_at: 2026-09-16T09:02:52Z
parent: badgersbay-ucgi
---

Verify against an archive from the current honeybadger client, not a
hand-rolled one:

    findings reach the record and the view
    completeness unchanged with and without an inventory
    an unknown schema_version is stored and rendered
    malformed JSON does not fail the submission
    an archive without an inventory still submits and shows unknown
    a submission from a current client answers 200, not 207

That last one is the regression this fixes, so it needs a test of its own.

Tasks 4.1 to 4.5 in the OpenSpec change.
