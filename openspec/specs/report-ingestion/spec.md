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
| `report_type` | Header `X-Report-Type` or JSON `report_type` | Yes | Report type: lynis, trivy, vulnix, neofetch |

## Validation Rules

### Report Type Validation

**Valid types:** `lynis`, `trivy`, `vulnix`, `neofetch` (case-insensitive)

**Error response (HTTP 400):**
```
Invalid report type '<type>'. Supported types: lynis, trivy, vulnix, neofetch
```

### JSON Format Validation

All reports must be valid JSON. Malformed JSON returns HTTP 400.

### Report Structure Validation

#### Lynis Reports

**Expected fields:**
- `report_version` OR `lynis_version`

**Behavior:** Warning logged if missing, but report accepted (allows version flexibility)

#### Trivy Reports

**Required fields:**
- `SchemaVersion` (required)
- `ArtifactName` (required)

**Error if missing:**
```
Invalid Trivy report: missing required fields: SchemaVersion, ArtifactName
```

#### Vulnix Reports

**Expected structure:** JSON object or array

**Error if invalid:**
```
Invalid Vulnix report: must be a JSON object or array
```

#### Neofetch Reports

**Expected structure:** JSON object

**Expected fields (warning if none present):**
- `hostname`
- `os`
- `kernel`
- `system`

**Note:** At least one system info field should be present

## Response Format

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

## Known Limitations

- No authentication/authorization
- No rate limiting
- No duplicate detection (overwrites by date)
- No report size limits
- No async processing (blocking I/O)
