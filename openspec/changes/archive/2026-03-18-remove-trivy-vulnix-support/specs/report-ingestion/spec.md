## MODIFIED Requirements

### Requirement: Report Type Validation

The server SHALL accept only `lynis` and `neofetch` report types (case-insensitive).

#### Scenario: Valid Lynis report type
- **WHEN** client submits report with `X-Report-Type: lynis`
- **THEN** server accepts the report for validation

#### Scenario: Valid Neofetch report type
- **WHEN** client submits report with `X-Report-Type: neofetch`
- **THEN** server accepts the report for validation

#### Scenario: Invalid Trivy report type
- **WHEN** client submits report with `X-Report-Type: trivy`
- **THEN** server responds with HTTP 400 and message "Invalid report type 'trivy'. Supported types: lynis, neofetch"

#### Scenario: Invalid Vulnix report type
- **WHEN** client submits report with `X-Report-Type: vulnix`
- **THEN** server responds with HTTP 400 and message "Invalid report type 'vulnix'. Supported types: lynis, neofetch"

#### Scenario: Case insensitive type matching
- **WHEN** client submits report with `X-Report-Type: LYNIS`
- **THEN** server accepts the report (case normalized to lowercase)

## REMOVED Requirements

### Requirement: Trivy Report Structure Validation
**Reason**: Trivy scanning is not required for ISO compliance use case
**Migration**: Remove Trivy scan submission from client scripts. Use only Lynis for system hardening checks.

### Requirement: Vulnix Report Structure Validation
**Reason**: Vulnix (NixOS-specific) scanning is not required for ISO compliance use case
**Migration**: Remove Vulnix scan submission from client scripts. Use only Lynis for system hardening checks.
