---
# badgersbay-9k2u
title: Write the findings into the submission record
status: completed
type: task
priority: high
tags:
    - badgersbay
created_at: 2026-09-16T09:02:52Z
updated_at: 2026-09-16T09:12:55Z
parent: badgersbay-ucgi
---

Parse the findings into \`submission.json\` as \`inventory\`, beside the asset ID,
owner and class already recorded there. Same reason those are denormalised: the
register moves, the client moves, and a closed round has to keep reporting what
was true when it was scanned.

Keep the whole document under \`inventory_raw\`. The client runs ahead of the
server and will keep doing so - it already emits fields this change does not
model. Storing only what is modelled today would throw away the rest at the
door, which is the mistake this whole line of work exists to correct.

An unknown \`schema_version\` is stored and used for the fields the server
understands, not refused: the submission is evidence regardless, and refusing
would take the fleet out of the dashboard on a client upgrade.

Malformed JSON is logged and skipped, never fatal to the submission.

Tasks 2.1 to 2.4 in the OpenSpec change.


## Summary of Changes

`store_submission()` takes an `inventory=` argument. `submission.json` gains `inventory` (the parsed findings, via the new module-level `parse_asset_inventory()`) and `inventory_raw` (the document whole). The document is also written to the record directory as `asset-inventory.json`, which makes it downloadable through the existing `/evidence/` route without further work. An unknown `schema_version` is logged and kept; a document with no usable findings is logged, stored whole, and recorded with no findings.
