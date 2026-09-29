## 1. Recognise The Report

- [x] 1.1 Add a pure function that decides whether bytes are a HardeningKitty result by its header,
      tolerating a byte order mark; verify with doctests for the real header, a header with a BOM,
      an empty file and an unrelated CSV
- [x] 1.2 Recognise `hardeningkitty.csv` in `detect_report_type_from_filename()` and keep it out of
      the `json.loads()` path in `extract_and_validate_tar()`; an invalid one goes to
      `unrecognised` with its reason; verify with the test-laptop archive and a doctored copy
- [x] 1.3 Store it as `hardeningkitty.csv` beside the archive and add `'hardeningkitty'` to
      `REPORT_FILENAMES`; verify an end-to-end submission of the test-laptop archive to a server on
      an ephemeral port records `reports: [fastfetch, hardeningkitty]` and is complete for a
      register entry of class `windows`

## 2. Repair Stored Records

- [x] 2.1 Add the startup repair described in `design.md`, run before the index is built; verify
      on a storage tree holding a record written by the current code from the test-laptop archive,
      with `hardeningkitty` removed from its `reports`, that one start restores it, writes the
      file, changes no other field, and logs the record
- [x] 2.2 Verify a second start opens no archive for that record and changes nothing
- [x] 2.3 Verify a Windows record whose archive has no `hardeningkitty.csv`, and a Linux record,
      are left byte-identical

## 3. Documentation

- [x] 3.1 Update `CLAUDE.md` (report types table and the "OK" logic, which still names Trivy or
      Vulnix as required) and `README.md` where report types are listed
- [x] 3.2 Add a CHANGELOG entry under `## NEXT VERSION`, noting that stored Windows records are
      repaired once at startup and that closed rounds may show those assets complete
