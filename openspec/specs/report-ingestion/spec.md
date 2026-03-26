# Report Ingestion

## Overview

The server accepts security scan reports via HTTP POST and validates them before storage.

## HTTP API

### Endpoint

```
POST /
Content-Type: application/json
```

### Input Methods

#### Option 1: HTTP Headers (Recommended)

```bash
curl -X POST http://server:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-Report-Type: lynis" \
  -d @/path/to/report.json
```

#### Option 2: JSON Body Fields

```json
{
  "hostname": "webserver01",
  "username": "admin",
  "report_type": "lynis",
  "scan_data": {...}
}
```

### Required Fields

| Field | Source | Required | Description |
|-------|--------|----------|-------------|
| `hostname` | Header `X-Hostname` or JSON `hostname` | Yes | Hostname of scanned machine |
| `username` | Header `X-Username` or JSON `username` | Yes | User who performed scan |
| `report_type` | Header `X-Report-Type` or JSON `report_type` | Yes | Report type: lynis, neofetch |

## Validation Rules

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

### JSON Format Validation

All reports must be valid JSON. Malformed JSON returns HTTP 400.

### Report Structure Validation

#### Lynis Reports

**Expected fields:**
- `report_version` OR `lynis_version`

**Behavior:** Warning logged if missing, but report accepted (allows version flexibility)

#### Neofetch Reports

**Expected structure:** JSON object

**Expected fields (warning if none present):**
- `hostname`
- `os`
- `kernel`
- `system`

**Note:** At least one system info field should be present

## Response Format

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

### Success (HTTP 200)

```json
{
  "status": "success",
  "message": "Report saved successfully",
  "path": "./reports/hostname-username-20260316/lynis-report.json"
}
```

### Client Errors (HTTP 400)

- Missing required fields
- Invalid report type
- Invalid JSON format
- Invalid report structure

### Server Errors (HTTP 500)

- Storage failures
- Unexpected exceptions

## Implementation Location

- Handler: `honeybadger_server.py:ReportHandler.do_POST()` (line 160)
- Validation:
  - Type: `validate_report_type()` (line 59)
  - Structure: `validate_report_structure()` (line 66)
- Storage: `save_report()` (line 224)

## ADDED Requirements

### Requirement: Accept OS-Type header

The system SHALL accept an optional X-OS-Type header to identify the operating system of the client.

#### Scenario: OS type provided
- **WHEN** client sends header `X-OS-Type: ubuntu`
- **THEN** system accepts and stores os_type metadata

#### Scenario: OS type not provided
- **WHEN** client omits X-OS-Type header
- **THEN** system continues processing without error (header is optional)

#### Scenario: OS type in success response
- **WHEN** upload succeeds with X-OS-Type header
- **THEN** success response includes os_type in metadata

### Requirement: Calculate target audit period

The system SHALL calculate which audit period an upload belongs to based on upload date and configured audit months.

#### Scenario: Upload during audit month
- **WHEN** upload received on 2026-03-15 and audit_months is [3, 9]
- **THEN** target audit period is "2026-03"

#### Scenario: Upload between audit months
- **WHEN** upload received on 2026-04-10 and audit_months is [3, 9]
- **THEN** target audit period is "2026-09"

#### Scenario: Upload after last audit month
- **WHEN** upload received on 2026-10-05 and audit_months is [3, 9]
- **THEN** target audit period is "2027-03"

### Requirement: Include audit period in response

The system SHALL include the target audit period in the success response.

#### Scenario: Success response with audit period
- **WHEN** upload succeeds in compliance mode
- **THEN** response includes `"audit_period": "2026-03"`

#### Scenario: Legacy mode response
- **WHEN** upload succeeds in legacy mode (compliance disabled)
- **THEN** response does not include audit_period field

## Known Limitations

- No authentication/authorization
- No rate limiting
- No duplicate detection (overwrites by date)
- No report size limits
- No async processing (blocking I/O)
