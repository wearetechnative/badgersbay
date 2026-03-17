## REMOVED Requirements

### Requirement: Include SID in response

**Reason**: SID is being removed from the system. Hostname is more reliable and meaningful for operators.

**Migration**: API consumers should use `hostname` field instead of `sid` field.

**Original requirement:**
The system SHALL include the SID in success response when compliance mode is enabled.

## MODIFIED Requirements

### Requirement: Success response includes storage path

The system SHALL return the storage path in success responses, reflecting the storage mode and using hostname-based paths.

#### Scenario: Compliance mode success response
- **WHEN** upload succeeds in compliance mode
- **THEN** response path is `./reports/2026-03/webserver01-admin/lynis-report.json`

#### Scenario: Legacy mode success response
- **WHEN** upload succeeds in legacy mode
- **THEN** response path is `./reports/webserver01-admin-20260316/lynis-report.json`

#### Scenario: Response includes hostname not SID
- **WHEN** upload succeeds in any mode
- **THEN** response does NOT include `sid` field

### Requirement: Success response structure

The system SHALL return a JSON response with storage metadata on successful upload.

#### Scenario: Compliance mode response fields
- **WHEN** upload succeeds with compliance enabled
- **THEN** response includes:
  - `status`: "success"
  - `message`: "Report saved successfully"
  - `path`: storage path using hostname-username
  - `audit_period`: calculated audit period (YYYY-MM)
  - `os_type`: OS type from X-OS-Type header or "unknown"

#### Scenario: Legacy mode response fields
- **WHEN** upload succeeds with compliance disabled
- **THEN** response includes:
  - `status`: "success"
  - `message`: "Report saved successfully"
  - `path`: storage path using hostname-username-date

#### Scenario: No SID field in response
- **WHEN** any upload succeeds
- **THEN** response does NOT contain `sid` field
