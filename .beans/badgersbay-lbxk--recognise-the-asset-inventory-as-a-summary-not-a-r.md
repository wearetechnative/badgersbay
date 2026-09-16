---
# badgersbay-lbxk
title: Recognise the asset inventory as a summary, not a report
status: completed
type: task
priority: high
tags:
    - badgersbay
created_at: 2026-09-16T09:02:52Z
updated_at: 2026-09-16T09:12:55Z
parent: badgersbay-ucgi
---

\`asset-inventory.json\` is a JSON member, so it reaches
\`detect_report_type_from_filename()\`, which returns None and reports it as
unrecognised - every submission from a current client answers 207 for it.

Recognise it by filename, extract it, and store it in the submission record.

Keep it out of the requirement set. Treating it as a report type would make it
count toward completeness, and an older client that does not send it would
become incomplete for a reason its owner cannot act on - the same trap Windows
assets fell into before they were reported as manual.

Tasks 1.1 to 1.4 in the OpenSpec change.


## Summary of Changes

`asset-inventory.json` is recognised by filename in `extract_and_validate_tar()` and carried out as `extraction['inventory']`, separate from `reports`. `detect_report_type_from_filename()` returns None for it explicitly, so it can never fall through to a pattern match. It is written into the submission record beside the reports and never enters `saved_reports`, so `evaluate_completeness()` is untouched by it.
