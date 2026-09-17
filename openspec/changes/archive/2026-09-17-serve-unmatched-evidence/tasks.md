# Tasks

## 1. Route

- [x] 1.1 A pure function splitting an `/evidence/` path into tree, key, record
      and filename, with the tree an allowlist and doctests for both accepted
      shapes
- [x] 1.2 Reject the period archive, an unknown tree, and any segment that
      climbs
- [x] 1.3 Resolve against the named tree, keeping the containment check

## 2. Links

- [x] 2.1 Build hrefs from `record_dir` rather than the register serial
- [x] 2.2 One badge builder shared by the round table and the unmatched block
- [x] 2.3 Link the reports and the archive beside each unmatched row, under its
      reason

## 3. Verify

- [x] 3.1 Doctests
- [x] 3.2 An unmatched submission downloads, and is named for its serial
- [x] 3.3 The round view carries the link, beside the right reason
- [x] 3.4 A period-archive path is refused by the route
- [x] 3.5 The three-segment form still serves a matched record
- [x] 3.6 `openspec validate --strict`
