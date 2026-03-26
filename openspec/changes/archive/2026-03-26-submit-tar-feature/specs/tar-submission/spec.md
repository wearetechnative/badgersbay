# Tar Submission

## Overview

The server accepts tar archives containing multiple security scan reports via HTTP POST, extracts and validates individual reports, then stores them using the existing storage system.

## HTTP API

### Endpoint

```
POST /submit-tar
Content-Type: application/x-tar
```

### Example

```bash
# Create tar with reports
tar -czf reports.tar.gz lynis-report.json neofetch-report.json trivy-report.json

# Submit to server
curl -X POST http://server:7123/submit-tar \
  -H "Content-Type: application/x-tar" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  --data-binary @reports.tar.gz
```

### Required Headers

| Header | Required | Description |
|--------|----------|-------------|
| `X-Hostname` | Yes | Hostname of scanned machine |
| `X-Username` | Yes | User who performed scan |
| `Content-Type` | Yes | Must be `application/x-tar` or `application/gzip` |

## ADDED Requirements

### Requirement: Tar Archive Validation

The server SHALL validate tar archive structure and contents before extraction.

#### Scenario: Valid tar archive accepted
- **WHEN** client submits a valid tar file with JSON reports
- **THEN** server extracts and processes all contained reports

#### Scenario: Reject corrupted tar files
- **WHEN** client submits corrupted or truncated tar data
- **THEN** server responds with HTTP 400 and message "Invalid tar archive: corrupted data"

#### Scenario: Reject empty tar archives
- **WHEN** client submits empty tar archive with no files
- **THEN** server responds with HTTP 400 and message "Tar archive contains no report files"

### Requirement: Path Traversal Protection

The server SHALL reject tar archives containing path traversal attacks or absolute paths.

#### Scenario: Reject absolute paths
- **WHEN** tar contains file with absolute path `/etc/passwd`
- **THEN** server responds with HTTP 400 and message "Tar archive contains dangerous path: /etc/passwd"

#### Scenario: Reject parent directory traversal
- **WHEN** tar contains file with path `../../etc/passwd`
- **THEN** server responds with HTTP 400 and message "Tar archive contains dangerous path: ../../etc/passwd"

#### Scenario: Accept safe relative paths
- **WHEN** tar contains files like `lynis-report.json` or `reports/lynis.json`
- **THEN** server extracts and processes the files normally

### Requirement: File Type Detection

The server SHALL identify report types from filenames within the tar archive.

#### Scenario: Detect lynis report from filename
- **WHEN** tar contains file named `lynis-report.json` or `lynis.json`
- **THEN** server processes it as report type "lynis"

#### Scenario: Detect neofetch report from filename
- **WHEN** tar contains file named `neofetch-report.json` or `neofetch.json`
- **THEN** server processes it as report type "neofetch"

#### Scenario: Detect trivy report from filename
- **WHEN** tar contains file named `trivy-report.json` or `trivy.json`
- **THEN** server processes it as report type "trivy"

#### Scenario: Detect vulnix report from filename
- **WHEN** tar contains file named `vulnix-report.json` or `vulnix.json`
- **THEN** server processes it as report type "vulnix"

#### Scenario: Ignore non-JSON files
- **WHEN** tar contains files like `README.txt` or `scan.sh`
- **THEN** server skips these files and only processes JSON files

#### Scenario: Reject unrecognized JSON files
- **WHEN** tar contains `unknown-tool.json` that doesn't match known patterns
- **THEN** server responds with HTTP 400 and message "Cannot determine report type for file: unknown-tool.json"

### Requirement: Multi-Report Processing

The server SHALL process all valid JSON reports from the tar archive and report results.

#### Scenario: Successfully process all reports
- **WHEN** tar contains `lynis.json`, `neofetch.json`, and `trivy.json` (all valid)
- **THEN** server responds with HTTP 200 and JSON listing all successful saves

#### Scenario: Partial failure with error reporting
- **WHEN** tar contains valid `lynis.json` but invalid `neofetch.json`
- **THEN** server responds with HTTP 207 Multi-Status listing successes and failures separately

#### Scenario: Complete failure if all invalid
- **WHEN** tar contains only invalid or corrupted JSON files
- **THEN** server responds with HTTP 400 and lists all validation errors

### Requirement: Report Size Limits

The server SHALL enforce maximum tar archive and individual file sizes to prevent resource exhaustion.

#### Scenario: Accept tar within size limit
- **WHEN** client submits tar archive under 50MB
- **THEN** server processes the archive normally

#### Scenario: Reject oversized tar archives
- **WHEN** client submits tar archive over 50MB
- **THEN** server responds with HTTP 413 and message "Tar archive too large (max 50MB)"

#### Scenario: Reject oversized individual files
- **WHEN** tar contains a single JSON file over 10MB
- **THEN** server responds with HTTP 400 and message "File too large: lynis-report.json (max 10MB per file)"

## Response Format

### Success (HTTP 200)

```json
{
  "status": "success",
  "message": "Processed 3 reports from tar archive",
  "results": [
    {
      "file": "lynis-report.json",
      "type": "lynis",
      "status": "saved",
      "path": "./reports/hostname-username-20260316/lynis-report.json"
    },
    {
      "file": "neofetch-report.json",
      "type": "neofetch",
      "status": "saved",
      "path": "./reports/hostname-username-20260316/neofetch-report.json"
    },
    {
      "file": "trivy-report.json",
      "type": "trivy",
      "status": "saved",
      "path": "./reports/hostname-username-20260316/trivy-report.json"
    }
  ]
}
```

### Partial Success (HTTP 207 Multi-Status)

```json
{
  "status": "partial",
  "message": "Processed 2/3 reports, 1 failed",
  "results": [
    {
      "file": "lynis-report.json",
      "type": "lynis",
      "status": "saved",
      "path": "./reports/hostname-username-20260316/lynis-report.json"
    },
    {
      "file": "neofetch-report.json",
      "type": "neofetch",
      "status": "error",
      "error": "Invalid neofetch structure: missing required fields"
    },
    {
      "file": "trivy-report.json",
      "type": "trivy",
      "status": "saved",
      "path": "./reports/hostname-username-20260316/trivy-report.json"
    }
  ]
}
```

### Client Errors (HTTP 400)

- Missing required headers (X-Hostname, X-Username)
- Invalid tar archive structure
- Path traversal attempts
- Unrecognized file types
- All reports failed validation

### Server Errors (HTTP 500)

- Storage failures
- Unexpected extraction errors

## Compression Support

### Requirement: Transparent Decompression

The server SHALL automatically detect and decompress gzip-compressed tar archives.

#### Scenario: Process gzip-compressed tar
- **WHEN** client submits `.tar.gz` file with gzip compression
- **THEN** server decompresses and processes contents normally

#### Scenario: Process uncompressed tar
- **WHEN** client submits `.tar` file without compression
- **THEN** server processes contents normally

#### Scenario: Detect compression from content
- **WHEN** client submits gzip file regardless of Content-Type header
- **THEN** server detects gzip magic bytes and decompresses automatically
