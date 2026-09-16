---
# badgersbay-lbxk
title: Recognise the asset inventory as a summary, not a report
status: todo
type: task
priority: high
tags:
    - badgersbay
created_at: 2026-09-16T09:02:52Z
updated_at: 2026-09-16T09:02:52Z
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
