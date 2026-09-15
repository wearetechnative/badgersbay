# Report Completeness Validation

## Purpose
Defines when a system's set of submitted reports counts as complete, how the
required set is configured, how completeness is tracked per audit period, and
how missing reports are reported back.

## Requirements

### Requirement: Define complete report set

The system SHALL define a complete report set as containing all mandatory reports plus at least one security scanner report.

#### Scenario: Complete set with Trivy
- **WHEN** system directory contains fastfetch-report.json, lynis-report.json, and trivy-report.json
- **THEN** report set is marked as complete

#### Scenario: Complete set with Vulnix
- **WHEN** system directory contains fastfetch-report.json, lynis-report.json, and vulnix-report.json
- **THEN** report set is marked as complete

#### Scenario: Complete set with both scanners
- **WHEN** system directory contains fastfetch-report.json, lynis-report.json, trivy-report.json, and vulnix-report.json
- **THEN** report set is marked as complete (having both is acceptable)

#### Scenario: Incomplete - missing security scanner
- **WHEN** system directory contains only fastfetch-report.json and lynis-report.json
- **THEN** report set is marked as incomplete with reason "Missing security scanner (trivy or vulnix required)"

#### Scenario: Incomplete - missing lynis
- **WHEN** system directory contains fastfetch-report.json and trivy-report.json but not lynis-report.json
- **THEN** report set is marked as incomplete with reason "Missing lynis-report.json"

#### Scenario: Incomplete - missing fastfetch
- **WHEN** system directory contains lynis-report.json and trivy-report.json but not fastfetch-report.json
- **THEN** report set is marked as incomplete with reason "Missing fastfetch-report.json"

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

### Requirement: Track completeness per audit period

The system SHALL track report completeness separately for each audit period.

#### Scenario: Complete in one period, incomplete in another
- **WHEN** webserver01 has complete set in 2026-03/ but incomplete set in 2026-09/
- **THEN** system shows complete for March period and incomplete for September period

#### Scenario: Multiple uploads within period
- **WHEN** webserver01 uploads incomplete set on day 1 and complete set on day 5 (same period)
- **THEN** system shows latest status (complete) for that period

### Requirement: Identify missing reports

The system SHALL identify which specific reports are missing from an incomplete set.

#### Scenario: List missing reports
- **WHEN** system directory has fastfetch and lynis but no scanner
- **THEN** system reports "Missing: trivy or vulnix"

#### Scenario: Multiple missing reports
- **WHEN** system directory has only fastfetch
- **THEN** system reports "Missing: lynis, trivy or vulnix"

#### Scenario: Complete set shows no missing
- **WHEN** system directory has complete report set
- **THEN** system reports no missing files
