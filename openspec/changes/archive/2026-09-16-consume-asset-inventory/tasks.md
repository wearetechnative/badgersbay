## 1. Extraction

- [x] 1.1 Recognise `asset-inventory.json` by filename, distinct from a report
      type
- [x] 1.2 Extract and store it in the submission record
- [x] 1.3 It does not count toward completeness, and its absence is not a
      missing requirement
- [x] 1.4 A submission carrying one stops reporting an unrecognised member

## 2. The record

- [x] 2.1 Parse the findings into `submission.json` as `inventory`
- [x] 2.2 Keep the whole document under `inventory_raw`
- [x] 2.3 Record `schema_version` and keep a document whose version is unknown
- [x] 2.4 A malformed inventory is logged and skipped, never fatal to the
      submission

## 3. Fleet view

- [x] 3.1 Columns: disk encryption, screen lock, firewall, hardening score,
      OS up-to-date
- [x] 3.2 A `null` value renders as unknown with the client's finding, not as
      blank
- [x] 3.3 An asset with no inventory renders as unknown, not as a failure
- [x] 3.4 The finding is available on the row, so a value can be traced without
      opening the archive
- [x] 3.5 No colour judgement on the values; the client's finding text carries
      its own verdict

## 4. Tests

- [x] 4.1 A real archive from the current client yields the findings
- [x] 4.2 Completeness is unchanged by the presence or absence of an inventory
- [x] 4.3 An unknown `schema_version` is stored and rendered
- [x] 4.4 Malformed JSON does not fail the submission
- [x] 4.5 An archive without an inventory still submits and shows unknown

## 5. Docs

- [x] 5.1 `README.md`: what the columns come from and what unknown means
- [x] 5.2 `CLAUDE.md`: the record now carries findings
- [x] 5.3 `CHANGELOG.md` under NEXT VERSION
