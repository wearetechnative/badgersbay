## ADDED Requirements

### Requirement: Define complete report set

The system SHALL define a complete report set as containing all mandatory reports plus at least one security scanner report.

#### Scenario: Complete set with Trivy
- **WHEN** system directory contains neofetch-report.json, lynis-report.json, and trivy-report.json
- **THEN** report set is marked as complete

#### Scenario: Complete set with Vulnix
- **WHEN** system directory contains neofetch-report.json, lynis-report.json, and vulnix-report.json
- **THEN** report set is marked as complete

#### Scenario: Complete set with both scanners
- **WHEN** system directory contains neofetch-report.json, lynis-report.json, trivy-report.json, and vulnix-report.json
- **THEN** report set is marked as complete (having both is acceptable)

#### Scenario: Incomplete - missing security scanner
- **WHEN** system directory contains only neofetch-report.json and lynis-report.json
- **THEN** report set is marked as incomplete with reason "Missing security scanner (trivy or vulnix required)"

#### Scenario: Incomplete - missing lynis
- **WHEN** system directory contains neofetch-report.json and trivy-report.json but not lynis-report.json
- **THEN** report set is marked as incomplete with reason "Missing lynis-report.json"

#### Scenario: Incomplete - missing neofetch
- **WHEN** system directory contains lynis-report.json and trivy-report.json but not neofetch-report.json
- **THEN** report set is marked as incomplete with reason "Missing neofetch-report.json"

### Requirement: Configure required reports

The system SHALL allow configuration of required reports via config.yaml.

#### Scenario: Configure mandatory reports
- **WHEN** config.yaml contains `compliance.required_reports.mandatory: [neofetch, lynis]`
- **THEN** both neofetch and lynis are required for all systems

#### Scenario: Configure one-of scanner requirement
- **WHEN** config.yaml contains `compliance.required_reports.one_of: [trivy, vulnix]`
- **THEN** at least one of trivy or vulnix is required

#### Scenario: Default configuration
- **WHEN** compliance.required_reports section is not specified
- **THEN** system defaults to mandatory: [neofetch, lynis] and one_of: [trivy, vulnix]

### Requirement: Track completeness per audit period

The system SHALL track report completeness separately for each audit period.

#### Scenario: Complete in one period, incomplete in another
- **WHEN** laptop-SN001 has complete set in 2026-03/ but incomplete set in 2026-09/
- **THEN** system shows complete for March period and incomplete for September period

#### Scenario: Multiple uploads within period
- **WHEN** laptop-SN001 uploads incomplete set on day 1 and complete set on day 5 (same period)
- **THEN** system shows latest status (complete) for that period

### Requirement: Identify missing reports

The system SHALL identify which specific reports are missing from an incomplete set.

#### Scenario: List missing reports
- **WHEN** system directory has neofetch and lynis but no scanner
- **THEN** system reports "Missing: trivy or vulnix"

#### Scenario: Multiple missing reports
- **WHEN** system directory has only neofetch
- **THEN** system reports "Missing: lynis, trivy or vulnix"

#### Scenario: Complete set shows no missing
- **WHEN** system directory has complete report set
- **THEN** system reports no missing files
