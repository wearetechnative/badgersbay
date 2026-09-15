## ADDED Requirements

### Requirement: Store fastfetch reports under a fixed filename

The system SHALL write an accepted fastfetch report to `fastfetch-report.json`
within the system directory for the audit period.

#### Scenario: Fastfetch report saved
- **WHEN** a client submits a report of type `fastfetch` for `lobos-wtoorren`
  in audit period 2026-09
- **THEN** the file is written to
  `reports/2026-09/lobos-wtoorren/fastfetch-report.json`

#### Scenario: Same-period resubmission overwrites
- **WHEN** the same system submits a fastfetch report twice within one audit
  period
- **THEN** the second submission overwrites the first

### Requirement: Retain legacy neofetch files

The system SHALL leave existing `neofetch-report.json` files on disk unchanged.

#### Scenario: Legacy file present
- **WHEN** a system directory contains `neofetch-report.json` from a previous
  client generation
- **THEN** the file is neither renamed nor deleted

#### Scenario: Legacy file not used as system information
- **WHEN** the compliance cache is rebuilt and a directory contains only
  `neofetch-report.json` as system information
- **THEN** the system reports OS type "unknown" and does not count the file
  toward completeness
