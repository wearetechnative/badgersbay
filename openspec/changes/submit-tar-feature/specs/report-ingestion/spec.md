# Report Ingestion (Delta)

## ADDED Requirements

### Requirement: Support Trivy and Vulnix Report Types

The server SHALL accept `trivy` and `vulnix` report types in addition to existing `lynis` and `neofetch` types.

#### Scenario: Valid Trivy report type
- **WHEN** client submits report with `X-Report-Type: trivy`
- **THEN** server accepts the report for validation

#### Scenario: Valid Vulnix report type
- **WHEN** client submits report with `X-Report-Type: vulnix`
- **THEN** server accepts the report for validation

#### Scenario: Case insensitive Trivy type
- **WHEN** client submits report with `X-Report-Type: TRIVY`
- **THEN** server accepts the report (case normalized to lowercase)

#### Scenario: Case insensitive Vulnix type
- **WHEN** client submits report with `X-Report-Type: VULNIX`
- **THEN** server accepts the report (case normalized to lowercase)

### Requirement: Trivy Report Structure Validation

The server SHALL validate Trivy container/OS vulnerability scan reports.

#### Scenario: Valid Trivy report with Results field
- **WHEN** Trivy report contains `Results` array field
- **THEN** server accepts the report

#### Scenario: Valid Trivy report with ArtifactName
- **WHEN** Trivy report contains `ArtifactName` string field
- **THEN** server accepts the report

#### Scenario: Warning on minimal Trivy report
- **WHEN** Trivy report is valid JSON but missing both `Results` and `ArtifactName`
- **THEN** server logs warning but accepts the report

### Requirement: Vulnix Report Structure Validation

The server SHALL validate Vulnix NixOS-specific vulnerability scan reports.

#### Scenario: Valid Vulnix report with vulnerabilities array
- **WHEN** Vulnix report contains `vulnerabilities` array field
- **THEN** server accepts the report

#### Scenario: Warning on minimal Vulnix report
- **WHEN** Vulnix report is valid JSON but missing `vulnerabilities` field
- **THEN** server logs warning but accepts the report

## MODIFIED Requirements

### Requirement: Report Type Validation

The server SHALL accept `lynis`, `neofetch`, `trivy`, and `vulnix` report types (case-insensitive).

#### Scenario: Valid Lynis report type
- **WHEN** client submits report with `X-Report-Type: lynis`
- **THEN** server accepts the report for validation

#### Scenario: Valid Neofetch report type
- **WHEN** client submits report with `X-Report-Type: neofetch`
- **THEN** server accepts the report for validation

#### Scenario: Valid Trivy report type
- **WHEN** client submits report with `X-Report-Type: trivy`
- **THEN** server accepts the report for validation

#### Scenario: Valid Vulnix report type
- **WHEN** client submits report with `X-Report-Type: vulnix`
- **THEN** server accepts the report for validation

#### Scenario: Invalid unknown report type
- **WHEN** client submits report with `X-Report-Type: unknown`
- **THEN** server responds with HTTP 400 and message "Invalid report type 'unknown'. Supported types: lynis, neofetch, trivy, vulnix"

#### Scenario: Case insensitive type matching
- **WHEN** client submits report with `X-Report-Type: LYNIS`
- **THEN** server accepts the report (case normalized to lowercase)
