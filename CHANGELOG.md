# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## NEXT VERSION

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

## 1.1.0

### Added

- **Mandatory authentication**: Bearer tokens for report submission and Basic
  Auth for the dashboard, with `/health` left open for monitoring
