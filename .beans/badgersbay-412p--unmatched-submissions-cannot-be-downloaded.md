---
# badgersbay-412p
title: Unmatched submissions cannot be downloaded
status: completed
type: bug
priority: normal
tags:
    - dashboard
    - evidence
created_at: 2026-09-17T14:39:08Z
updated_at: 2026-09-17T14:58:53Z
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


## Decision

Serve them. The dashboard already hands every registered asset's evidence to
anyone holding the one shared password, and an unmatched submission is evidence
of exactly the same kind - the difference is that nobody has yet said which
asset it belongs to. Both reasons the round view names are resolved by reading
what the machine sent, so withholding the file leaves the alert unanswerable.
Leaving it unreachable was never weighed against anything; it was the shape the
route happened to have.

## Tasks

- [x] A pure function splitting an /evidence/ path into (tree, key, record,
      filename), with the tree an allowlist rather than a path segment
- [x] Keep the three-segment form working - it means the serial-keyed tree, and
      it is every link the dashboard has emitted so far
- [x] Reject the read-only period archive and anything climbing out of a tree
- [x] Build hrefs from where a record was written rather than from the register
      serial, so an unmatched record can be linked at all
- [x] Link the reports and the archive beside each unmatched row in the round view
- [x] Doctests for the path shapes and the href builder
- [x] End-to-end tests: an unmatched download succeeds and is named for its
      serial, the round view carries the link, the period archive stays unserved
- [x] Specs: report-storage gains the route requirement and loses its note;
      asset-register gains the link scenario


## Summary of Changes

Served. The dashboard already hands every registered asset's evidence to anyone
holding the one shared password; an unmatched record is the same kind of file,
only less identified.

- `parse_evidence_path()` splits the segments after `/evidence/` into tree, key,
  record and filename. The tree is matched against `EVIDENCE_TREES` rather than
  used as a path component, so `2026-03/` - history the server reads and never
  writes - is not reachable, and a segment that climbs is refused before any
  file is opened. Three segments still mean the serial-keyed tree, so links
  already filed in a compliance sheet keep working.
- `evidence_href()` builds a link from `record_dir` rather than from
  `entry['serial']`. That is what gives a record with no register entry a link
  at all, and it removes a latent mismatch in the matched case where the
  register's spelling of a serial and the client's need not agree.
- `evidence_badges_html()` is now shared by the per-asset table and the
  unmatched block, so each unmatched submission's reports and archive sit beside
  the reason it was filed under. A record the route does not serve shows its
  badges as text rather than as a link that 404s.

Tests: `TestUnmatchedEvidenceIsReachable` and
`TestEvidenceRouteRefusesWhatItDoesNotServe` in `test_asset_inventory.py`, plus
doctests on both new functions. 35 tests, all passing.

OpenSpec: `2026-09-17-serve-unmatched-evidence`, archived. `report-storage`
gains the route requirement and loses the note saying the route did not exist;
`asset-register` gains the scenario linking evidence to the reason.
