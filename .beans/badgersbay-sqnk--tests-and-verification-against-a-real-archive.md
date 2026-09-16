---
# badgersbay-sqnk
title: Tests and verification against a real archive
status: completed
type: task
priority: normal
tags:
    - badgersbay
created_at: 2026-09-16T09:02:52Z
updated_at: 2026-09-16T09:18:09Z
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


## Summary of Changes

`test_asset_inventory.py`: 16 end-to-end tests. Each starts a real server on an ephemeral port against a throwaway storage tree and a throwaway register, and submits real archives over HTTP.

The fixture `test-archive-current-client.tar.gz` is a real archive from the current honeybadger client; its `asset-inventory.json` was produced by the client's own `generate_xlsx_asset_row_report` run against its own output directory, not written by hand.

`test_answers_200_with_no_unrecognised_member` is the regression test. Verified it fails on the pre-change code with exactly `207 != 200` and `{'file': '.../asset-inventory.json', 'reason': 'Unrecognised report type'}`.

Also covered: findings reach the record and the view; the whole document survives; the inventory downloads through /evidence/; completeness unchanged with and without an inventory; requirements never name the inventory; an archive without one, and an asset never seen, both read unknown; a declined value reads unknown with its reason; an unknown schema_version is stored and rendered; malformed JSON is logged and skipped without failing the submission; a document with no findings is still kept whole; no finding cell carries a verdict class.

Pure functions carry doctests (43 passing). `nix flake check` passes.
