# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## NEXT VERSION

### Added

- **Accounting for an asset that cannot be scanned.** A control on each
  outstanding row records a reason, and the asset moves to a third category:
  `scanned / accounted for / outstanding`. Counting an accounted-for asset as
  scanned would fold "we hold evidence" together with "we hold an excuse", and
  the deviation count is what the ISO tool needs as its own figure.
  - Keyed on asset and round, so nothing carries over when the next round opens
  - A submission always wins: if the asset submits after all, the exception
    lapses without anyone withdrawing it
  - Stored beside the reports, so it survives a restart and can be handed to an
    auditor
  - The name recorded is self-reported and labelled as such; the dashboard uses
    one shared password
- **`--asset-register PATH`** overrides the register named in the config file,
  so a deployment can point at an agenix secret without editing the generated
  config.
- **Disappeared assets are reported.** The previously loaded register is
  remembered, and an asset that vanishes from a later one is named on the
  dashboard. A filtered or truncated export silently raises the coverage rate,
  which is the one direction a compliance figure must never move by accident.
  The server still starts: taking the portal down mid-round because two laptops
  were retired is worse than the risk.

### Added

- **Report extraction from tar archives**: `POST /submit-tar` now reads the
  reports out of the archive instead of only filing it away
  - Recognised JSON members are stored next to the archive under their normal
    names, so a bundled submission counts toward completeness like individual
    uploads do
  - The archive itself is still stored whole and unchanged as the evidence of
    record; non-JSON members such as `hardware-serial.txt` are left in it
  - OS type is read from the archive's fastfetch report; the `X-OS-Type` header
    is now only a fallback for archives without one
- **Per-file submission status**: a submission reports what happened to each
  member rather than standing or falling as a whole
  - HTTP 200 when every JSON member was recognised and stored
  - HTTP 207 Multi-Status when some were not, naming each one; the recognised
    reports are still saved and the archive is still stored
  - HTTP 400 only when the archive itself is unusable, and 413 when it exceeds
    50MB — in both cases nothing is stored
- **Tar submission specification**: the `tar-submission` capability is now
  written down in `openspec/specs/`, covering storage, extraction, per-file
  status, OS type resolution and archive limits

### Changed

- **Fastfetch replaces neofetch as the system information report**: the client
  emits `fastfetch.json`, and the server now carries that single name
  - Accepted report types are `lynis`, `fastfetch`, `trivy`, `vulnix`; a
    submission of type `neofetch` is rejected as unknown
  - Reports are stored as `fastfetch-report.json`, and compliance requires
    `[fastfetch, lynis]` by default — update `config.yaml` before restarting
  - The dashboard badge is `F`, with the legend `F=Fastfetch, L=Lynis,
    TAR=Tar Archive`; `/health` counts `fastfetch` instead of `neofetch`
  - Existing `neofetch-report.json` files stay on disk as audit evidence; they
    are not renamed and no longer count as system information

### Fixed

- **Linux systems recorded as incomplete**: bundled submissions from current
  clients yielded no reports at all, so every system that uploads by tar was
  recorded as missing its whole report set for the running audit period
- **September audit period showing a March artifact**: a leftover test
  submission in `reports/2026-09/` made the new round look like it already had
  a system in it; it has been moved to the period it belongs to, `2026-03`
- **`/health` reporting zeros on a compliance-mode install**: the endpoint
  counted audit periods and called them reports, and looked for report files
  inside the period directories rather than inside the systems
  - statistics are now computed per storage mode: compliance mode counts
    systems under `reports/<period>/<system>/`, legacy mode keeps counting at
    the top level
  - `total_report_directories` counts systems rather than periods,
    `unique_hosts` is derived from the directory shape the active mode uses,
    and `reports_by_type` looks inside system directories
  - monitoring that alerted on these numbers has been seeing zeros; anything
    calibrated against zero needs revisiting

## 1.1.0

### Added

- **Mandatory authentication**: Bearer tokens for report submission and Basic
  Auth for the dashboard, with `/health` left open for monitoring
