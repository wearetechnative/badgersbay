## Why

Tar submissions are never opened. `do_POST_submit_tar()` validates that the
body is a tar, writes it to disk whole, and records the report type `tar` —
its own docstring says "saves tar.gz as-is without extraction". The extraction
subsystem exists but is unreachable: `extract_and_validate_tar()` has zero call
sites, and with it `detect_report_type_from_filename()`,
`validate_tar_member_path()` and `validate_tar_size_limits()`.

The consequence is that **every tar submission is recorded as incomplete**,
on every platform, regardless of what it contains:

    lobos | wtoorren | unknown | 2026-09-15 | TAR | Incomplete - Missing: lynis

That is how the honeybadger client submits, so it is how all six Linux assets
in the ISO register submit. The stored evidence shows it: in
`reports/2026-03/`, `lobos-wtoorren/` holds only `submission-*.tar.gz` with no
extracted reports, while `mustad-jumphost-root/` and `technative-casper-lucak/`
hold loose JSON files — those arrived through the single-report `POST /` path.

This was specified and archived as delivered. `2026-03-26-submit-tar-feature`
required that the server "extracts and validates individual reports, then
stores them using the existing storage system", with HTTP 207 Multi-Status for
partial success. Its `tar-submission` capability spec never landed in
`openspec/specs/`, so nothing could check the claim. `CLAUDE.md:316` still
documents the per-file status that does not exist.

The naming is the second defect and the reason the first cannot be fixed on its
own. The client emits `fastfetch.json`; `detect_report_type_from_filename()`
matches `neofetch` and returns `None` for it, and
`extract_and_validate_tar():738` rejects the **entire archive** when any JSON
member has no recognised type. Wiring extraction up without the rename would
turn every Linux submission from silently incomplete into an outright HTTP 400.

## What Changes

- **Connect the tar handler to the extraction it was specified to perform.**
  Detected reports are saved alongside the tar; the tar itself is still stored
  whole, because it is the evidence of record.
- **Unrecognised JSON members no longer reject the archive.** They are reported
  per file, per the HTTP 207 Multi-Status contract already specified.
- Accept `fastfetch.json` as the system information report; drop `neofetch`
  from the accepted report types
- Store it as `fastfetch-report.json`
- Read OS type from the extracted fastfetch report, falling back to the
  `X-OS-Type` header when no fastfetch member is present
- Default `compliance.required_reports.mandatory` becomes `[fastfetch, lynis]`
- Dashboard report badge `N` becomes `F`
- Create the missing `tar-submission` capability spec
- Move `reports/2026-09/future-test-testuser/` into `reports/2026-03/` so the
  running audit round starts empty

Existing `neofetch-report.json` files stay on disk as audit evidence. They are
not renamed, not served as system information, and do not count toward
completeness. The 2026-03 period is closed history; its evidence lives in the
stored tar archives.

## Capabilities

### New Capabilities
- `tar-submission`: what `POST /submit-tar` accepts, extracts, stores and
  reports — the capability the archived change created but never landed

### Modified Capabilities
- `report-ingestion`: accept `fastfetch`, reject `neofetch`
- `report-storage`: write `fastfetch-report.json`
- `report-completeness-validation`: mandatory set uses `fastfetch`
- `compliance-dashboard`: OS type source and badge letter
- `health-monitoring`: report type counts use `fastfetch`

## Impact

- **Systems that submitted by tar change status on the next submission.** They
  were incomplete because nothing was read; they become complete or incomplete
  on their actual contents. Previously stored tars are not re-processed.
- **Breaking for clients still sending neofetch.** That is the macOS output
  from before the client migration. Those systems must run a current client.
- **Existing reports**: 13 `neofetch-report.json` files remain on disk,
  3 of them from real machines. They become invisible to the dashboard.
  Accepted: the tar archives are the evidence of record.
- **Config**: `config.yaml` must be updated before restart, or the server keeps
  requiring a report type it can no longer receive.

## Non-goals

- Reading non-JSON members. `hardware-serial.txt` and `asset-inventory.json`
  are what `asset-register-identity` and the honeybadger change
  `emit-asset-inventory-json` need; this change keeps the existing JSON-only
  filter and records the limit in the spec.
- Re-processing tars already on disk.
- Serial-number identity, asset register, progress tracking. See
  `asset-register-identity`.
