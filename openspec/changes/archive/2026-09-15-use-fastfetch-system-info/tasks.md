## 1. Ingestion

- [x] 1.1 `detect_report_type_from_filename()`: match `fastfetch` + `.json`,
      return `fastfetch`; remove the `neofetch` branch
- [x] 1.2 `validate_report_type()` / `valid_types`: replace `neofetch` with
      `fastfetch`
- [x] 1.3 `validate_report_structure()`: apply the former neofetch structure
      check to `fastfetch`

## 2. Tar extraction

- [x] 2.1 Call `extract_and_validate_tar()` from `do_POST_submit_tar()`
- [x] 2.2 Save each detected report through `save_report()`, into the same
      directory as the stored tar
- [x] 2.3 Keep storing the tar archive whole, unchanged
- [x] 2.4 Replace the hard failure at `extract_and_validate_tar():738`: an
      unrecognised JSON member is reported, not a reason to reject the archive
- [x] 2.5 Respond HTTP 200 when every member was recognised, 207 with per-file
      status when some were not, 400 only when the archive itself is unusable
- [x] 2.6 Update the compliance cache per detected report type instead of the
      single `tar` entry
- [x] 2.7 Read OS type from the extracted fastfetch report; fall back to the
      `X-OS-Type` header when the archive carries no fastfetch member

## 3. Storage

- [x] 3.1 `save_report()`: map `fastfetch` to `fastfetch-report.json`
- [x] 3.2 Confirm the unknown-type fallback still warns rather than silently
      accepting

## 4. Completeness and cache

- [x] 4.1 `ComplianceCache.rebuild()`: read OS type from
      `fastfetch-report.json`
- [x] 4.2 `ComplianceCache.update_system()`: same
- [x] 4.3 `config.yaml`: `required_reports.mandatory: [fastfetch, lynis]`
- [x] 4.4 Config default in `Config.load()`: same

## 5. Dashboard

- [x] 5.1 `report_map` in `generate_compliance_dashboard_html()`:
      `{'fastfetch': 'F', 'lynis': 'L'}`
- [x] 5.2 Legend line: `F=Fastfetch, L=Lynis, TAR=Tar Archive`
- [x] 5.3 `generate_status_html()` (legacy view): same rename

## 6. Health and docs

- [x] 6.1 `get_health_status()`: report the fastfetch type
- [x] 6.2 `README.md`, `CLAUDE.md`: replace neofetch throughout; correct the
      "only 837 lines" claim while there (the file is 2186 lines)

## 7. Data move (conflict-free part only)

- [x] 7.1 `mv reports/2026-09/future-test-testuser reports/2026-03/`
      (`reports/` is gitignored, dus git mv is niet van toepassing)
- [x] 7.2 Confirm `reports/2026-09/` is empty and removed
- [x] 7.3 Do NOT touch the three legacy `*-2026MMDD` directories — see design

## 8. Verify

- [x] 8.1 Submit a real honeybadger tar from a Linux client; assert the system
      shows Complete, a populated OS type, and `fastfetch-report.json` plus
      `lynis-report.json` saved next to the stored archive
- [x] 8.2 Submit a tar containing an unrecognised JSON member; assert HTTP 207
      with per-file status, the known reports saved, and the archive stored
- [x] 8.3 Submit a tar containing `neofetch.json` only; assert it is reported
      as unrecognised and the system is recorded incomplete
- [x] 8.4 Assert the stored tar is byte-identical to what the client sent
- [x] 8.5 Restart and confirm the cache rebuild reports the expected count
- [x] 8.6 With `reports/2026-09/` removed, the dashboard defaults to 2026-03;
      the September period appears and is auto-selected on the first real
      submission of the round
- [x] 8.7 Exercise the archive limits against a real client tar: nesting depth,
      50MB archive, 10MB per member, 100 members
