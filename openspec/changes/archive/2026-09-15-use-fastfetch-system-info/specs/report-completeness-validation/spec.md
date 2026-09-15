## MODIFIED Requirements

### Requirement: Configure required reports

The system SHALL allow configuration of required reports via config.yaml, using
`fastfetch` as the system information report type.

#### Scenario: Configure mandatory reports
- **WHEN** config.yaml contains `compliance.required_reports.mandatory: [fastfetch, lynis]`
- **THEN** both fastfetch and lynis are required for all systems

#### Scenario: Configure one-of scanner requirement
- **WHEN** config.yaml contains a non-empty `compliance.required_reports.one_of`
- **THEN** at least one of the listed report types is required

#### Scenario: Default configuration
- **WHEN** the `compliance.required_reports` section is not specified
- **THEN** the system defaults to mandatory `[fastfetch, lynis]` and one_of `[]`

#### Scenario: Missing system information report
- **WHEN** a system directory contains `lynis-report.json` but no
  `fastfetch-report.json`
- **THEN** the report set is incomplete with reason "Missing fastfetch"

#### Scenario: Complete set
- **WHEN** a system directory contains `fastfetch-report.json` and
  `lynis-report.json`
- **THEN** the report set is marked complete
