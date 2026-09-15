## MODIFIED Requirements

### Requirement: Display OS type information

The system SHALL display OS type for each system, read from the stored
fastfetch report, updating immediately upon report upload.

#### Scenario: OS type from neofetch data
- **WHEN** a system directory contains `neofetch-report.json` from an earlier
  client generation and no `fastfetch-report.json`
- **THEN** the dashboard displays "unknown" and does not read the legacy file
  as system information

#### Scenario: OS type from fastfetch data
- **WHEN** a client uploads fastfetch data with `{"os": "NixOS 26.05 (Yarara)"}`
- **THEN** the dashboard displays "NixOS 26.05 (Yarara)" in the OS Type column

#### Scenario: OS type updates without server restart
- **WHEN** a client uploads a new fastfetch report with a different OS version
- **THEN** a dashboard refresh shows the updated OS type

#### Scenario: OS type from tar submission header
- **WHEN** a client submits a tar archive that carries no fastfetch member but
  does send an `X-OS-Type` header
- **THEN** the dashboard displays that value; the header is now a fallback,
  because an archive containing fastfetch data is read directly

#### Scenario: Unknown OS type
- **WHEN** a system has no fastfetch report, or one without an `os` field
- **THEN** the dashboard displays "unknown" for OS type

#### Scenario: Dashboard refresh retrieves latest OS type
- **WHEN** a user clicks refresh or auto-refresh triggers
- **THEN** the dashboard shows the current OS type from the cache without
  requiring a server restart

### Requirement: Display system compliance table in compliance mode

The system SHALL display a table showing compliance status for each system in the audit period using hostname instead of SID.

**Columns:**
- Hostname (from X-Hostname header)
- Username
- OS Type
- Upload Date (latest upload in period)
- Reports (badges: F L)
- Status (Complete/Incomplete with details)

#### Scenario: Complete system row in compliance mode
- **WHEN** webserver01 has a complete set in 2026-09
- **THEN** row shows: "webserver01 | admin | ubuntu | 2026-09-15 | F L | ✓ Complete"

#### Scenario: Incomplete system row in compliance mode
- **WHEN** dbserver02 is missing lynis in 2026-09
- **THEN** row shows: "dbserver02 | dbadmin | nixos | 2026-09-10 | F | ⚠ Missing: lynis"

#### Scenario: No SID column
- **WHEN** viewing the compliance dashboard table
- **THEN** the table does NOT include a SID column; Hostname is the first column

## ADDED Requirements

### Requirement: Report badge for fastfetch

The system SHALL render the system information report as badge `F` linking to
the stored `fastfetch-report.json`.

#### Scenario: Badge rendered for present report
- **WHEN** a system has `fastfetch-report.json` in the selected audit period
- **THEN** the Reports column shows badge `F` linking to that file

#### Scenario: Legend reflects current report types
- **WHEN** the dashboard renders its legend
- **THEN** it reads "F=Fastfetch, L=Lynis, TAR=Tar Archive"
