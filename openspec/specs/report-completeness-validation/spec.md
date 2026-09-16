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

The system SHALL define required reports by requirement name and platform
class, not by tool name.

#### Scenario: Configure mandatory reports
- **WHEN** config.yaml configures the mandatory requirements for a platform
  class
- **THEN** those requirements are required for every asset of that class

#### Scenario: Configure one-of scanner requirement
- **WHEN** a platform class configures a non-empty `one_of` list
- **THEN** at least one of the listed requirements must be satisfied

#### Scenario: Default configuration
- **WHEN** no per-class configuration is given
- **THEN** the system defaults to `sysinfo` and `hardening` as mandatory for
  every class

#### Scenario: Linux and macOS requirements
- **WHEN** a register entry has class `linux` or `macos`
- **THEN** a complete submission requires `sysinfo` (fastfetch.json) and
  `hardening` (lynis-report.json)

#### Scenario: Windows requirements
- **WHEN** a register entry has class `windows`
- **THEN** a complete submission requires `sysinfo` and `hardening`
  (hardeningkitty.csv)

#### Scenario: Class comes from the register
- **WHEN** determining which reports a submission must contain
- **THEN** the platform class is read from the asset register, not inferred
  from the submission contents

#### Scenario: Windows before client support exists
- **WHEN** a register entry has class `windows` and the client cannot yet
  submit
- **THEN** the asset is reported as `manual` rather than incomplete

#### Scenario: Missing system information report
- **WHEN** a submission satisfies `hardening` but carries nothing that
  satisfies `sysinfo`
- **THEN** the report set is incomplete with reason "Missing sysinfo"

#### Scenario: Complete set
- **WHEN** a submission satisfies every mandatory requirement for its platform
  class
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
