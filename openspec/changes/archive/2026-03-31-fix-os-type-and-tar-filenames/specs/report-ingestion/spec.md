## MODIFIED Requirements

### Requirement: Success response structure

The system SHALL return a JSON response with storage metadata on successful upload.

#### Scenario: Compliance mode response fields
- **WHEN** upload succeeds with compliance enabled
- **THEN** response includes:
  - `status`: "success"
  - `message`: "Report saved successfully"
  - `path`: storage path using hostname-username
  - `audit_period`: calculated audit period (YYYY-MM)
  - `os_type`: OS type extracted from neofetch data or X-OS-Type header or "unknown"

#### Scenario: Legacy mode response fields
- **WHEN** upload succeeds with compliance disabled
- **THEN** response includes:
  - `status`: "success"
  - `message`: "Report saved successfully"
  - `path`: storage path using hostname-username-date

#### Scenario: No SID field in response
- **WHEN** any upload succeeds
- **THEN** response does NOT contain `sid` field

## ADDED Requirements

### Requirement: Extract OS type from neofetch JSON data

The system SHALL extract OS type from neofetch report JSON data when report_type is "neofetch".

#### Scenario: OS type in neofetch data
- **WHEN** client uploads neofetch report with `{"os": "NixOS 24.05"}` in JSON payload
- **THEN** system extracts "NixOS 24.05" as os_type

#### Scenario: OS type priority order
- **WHEN** client uploads neofetch with both X-OS-Type header and JSON `os` field
- **THEN** system uses JSON `os` field value (authoritative source)

#### Scenario: Fallback to header when JSON missing os field
- **WHEN** client uploads neofetch without `os` field in JSON but includes X-OS-Type header
- **THEN** system uses X-OS-Type header value

#### Scenario: Default when neither source available
- **WHEN** client uploads neofetch without `os` field in JSON and without X-OS-Type header
- **THEN** system sets os_type to "unknown"

#### Scenario: Non-neofetch reports use header only
- **WHEN** client uploads lynis/trivy/vulnix report
- **THEN** system uses X-OS-Type header only (does not inspect JSON payload for os field)

### Requirement: Pass OS type to cache

The system SHALL pass extracted OS type to compliance cache when updating system metadata.

#### Scenario: Cache receives extracted OS type
- **WHEN** neofetch upload completes with extracted os_type "Ubuntu 22.04"
- **THEN** compliance cache is updated with os_type "Ubuntu 22.04"

#### Scenario: Cache update enables immediate dashboard refresh
- **WHEN** neofetch upload completes with extracted os_type
- **THEN** dashboard refresh shows updated OS type without server restart
