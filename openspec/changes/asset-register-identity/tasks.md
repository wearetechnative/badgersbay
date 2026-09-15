## 1. Asset register

- [x] 1.1 Define `assets.csv` columns: `asset_id, serial, owner, model, class,
      status, owner_since, valid_from, valid_to`
- [x] 1.2 Loader with fail-fast validation: duplicate active serial, unknown
      class, unknown status, empty serial, overlapping validity for one serial
- [x] 1.5 Allow several rows per `asset_id` with distinct serials and validity
      windows; `asset_id` is the identity, serial the lookup key
- [x] 1.6 `status: retired` excludes an entry from the round denominator while
      keeping it visible and keeping its history
- [x] 1.3 `config.yaml`: `compliance.asset_register: ./assets.csv`
- [x] 1.4 Startup logs the register size; absent register disables the round and
      fleet views rather than crashing

## 2. Serial as identity

- [ ] 2.1 Read `hardware-serial.txt` from the submitted tar
- [ ] 2.2 Normalise (trim, strip BOM, uppercase) before lookup
- [ ] 2.3 Resolve serial to register entry; unmatched submissions go to
      `reports/unmatched/<hostname>-<username>/<timestamp>/`
- [ ] 2.4 Submissions without a readable serial are treated as unmatched, not
      rejected — never lose an upload
- [x] 2.5 A usable serial is one non-empty token, no whitespace, matching no
      known placeholder (`Not available`, `Not available (VM or unknown
      hardware)`, `To Be Filled`, `O.E.M.`, `Default string`,
      `System Serial Number`, all zeroes)
- [ ] 2.6 Record `unmatched_reason`: `no_serial` or `serial_not_in_register`
- [x] 2.7 Unit tests over the real values found on compute2: `PF50L2MR`,
      `MP1Y69AC`, `Not available`, `Mac OS X<TAB>`, empty, absent

## 3. Storage layout

- [ ] 3.1 Write to `reports/submissions/<serial>/<timestamp>/`
- [ ] 3.2 Store the tar alongside the extracted reports
- [ ] 3.3 Never overwrite an existing timestamped record
- [ ] 3.4 Leave `reports/2026-03/` untouched and unwritten

## 4. Audit period

- [x] 4.1 Rewrite `get_audit_period()` to map backward to the most recent audit
      month at or before the date
- [x] 4.2 Classify each submission `on_time` or `late` relative to its round
- [x] 4.5 `grace_weeks` config value defines both the on_time/late boundary and
      the scan window used for scope membership
- [ ] 4.3 Remove audit period from all filesystem paths
- [x] 4.4 Doctests covering 2026-09-15, 2026-10-02, 2026-04-10, 2026-02-10

## 5. Completeness per class

- [ ] 5.1 Rename report types to `sysinfo` and `hardening`
- [ ] 5.2 Per-class requirement table in config
- [ ] 5.3 Windows assets report `manual` until `wtoorren-cikq` lands

## 6. Index

- [ ] 6.1 Rebuild the cache from `reports/submissions/` keyed on serial
- [ ] 6.2 Keep one record per submission with its timestamp; no collapsing
- [ ] 6.3 Read existing period directories (`reports/YYYY-MM/`) as archive
      records without serials — including `2026-09`, which holds the round that
      is running, so switching layout does not empty the round view

## 7. Round view

- [ ] 7.1 Determine the currently open round from today and `audit_months`
- [ ] 7.2 Row per register entry; LEFT JOIN against submissions in that round
- [ ] 7.3 Progress count, per-owner breakdown, outstanding list with last-seen
- [ ] 7.4 Unmatched submissions surfaced as a warning block, grouped by reason:
      missing serial (client problem) versus unknown serial (register problem)

## 8. Fleet view

- [ ] 8.1 Latest submission per register entry, regardless of round
- [ ] 8.2 Age relative to the current round: fresh / previous round / stale
- [ ] 8.3 Assets that have never submitted appear with "never seen"

## 9. Downloads

- [ ] 9.1 TAR download filename follows the register convention
      `<asset_id>-<YYYY-MM-DD>-<owner-slug>.tar.gz`

## 10. Docs

- [ ] 10.1 `README.md`: register setup, CSV format, layout
- [ ] 10.2 `CLAUDE.md`: new storage layout, corrected line count, retire the
      single-file principle explicitly

## 11. Register lifecycle

- [ ] 11.1 Scope membership from `valid_from`/`valid_to` overlapping the round's
      scan window; no snapshot file
- [ ] 11.2 Write `asset_id`, `owner` and `class` into each submission record at
      storage time; never join them at read time
- [ ] 11.3 Retired assets listed separately in the round view, excluded from the
      denominator
- [ ] 11.4 Assets entering scope inside the scan window count for that round;
      assets entering after it roll to the next and show in the fleet view as
      never audited
- [ ] 11.7 `valid_to` carries a reason; a departure without one is reported as
      unexplained rather than subtracted from the denominator
- [ ] 11.8 An asset that left scope unscanned counts as accounted for, never as
      scanned
- [ ] 11.5 Flag a submission whose `scanned_at` predates the asset's
      `owner_since` as evidence predating the current holder
- [ ] 11.6 Doctests: retirement mid-round, transfer mid-round, serial change,
      asset added mid-round
