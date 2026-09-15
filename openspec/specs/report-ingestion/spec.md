# Report Ingestion

## Purpose
Defines what the server returns when it accepts a report, and how system
information carried in a submission is extracted and handed to the compliance
cache.

## Requirements

### Requirement: Success response structure

The system SHALL return a JSON response with storage metadata on successful upload.

#### Scenario: Compliance mode response fields
- **WHEN** upload succeeds with compliance enabled
- **THEN** response includes:
  - `status`: "success"
  - `message`: "Report saved successfully"
  - `path`: storage path using hostname-username
  - `audit_period`: calculated audit period (YYYY-MM)
  - `os_type`: OS type extracted from fastfetch data or X-OS-Type header or "unknown"

#### Scenario: Legacy mode response fields
- **WHEN** upload succeeds with compliance disabled
- **THEN** response includes:
  - `status`: "success"
  - `message`: "Report saved successfully"
  - `path`: storage path using hostname-username-date

#### Scenario: No SID field in response
- **WHEN** any upload succeeds
- **THEN** response does NOT contain `sid` field


### Requirement: Extract OS type from fastfetch JSON data

The system SHALL extract the OS type from the `os` field of an uploaded
fastfetch report and pass it to the compliance cache.

#### Scenario: OS type present in fastfetch report
- **WHEN** a client uploads `fastfetch.json` containing `{"os": "NixOS 26.05 (Yarara)"}`
- **THEN** the system records OS type "NixOS 26.05 (Yarara)" for that system

#### Scenario: OS type priority order
- **WHEN** a client uploads fastfetch data with both an X-OS-Type header and a
  JSON `os` field
- **THEN** the system uses the JSON `os` field value (authoritative source)

#### Scenario: OS field absent
- **WHEN** an uploaded fastfetch report has no `os` field
- **THEN** the system records OS type "unknown" and accepts the report

#### Scenario: Fallback to header when JSON missing os field
- **WHEN** a client uploads fastfetch data without an `os` field but with an
  X-OS-Type header
- **THEN** the system uses the X-OS-Type header value

#### Scenario: Other report types use the header only
- **WHEN** a client uploads a lynis, trivy or vulnix report
- **THEN** the system uses the X-OS-Type header only, and does not inspect the
  JSON payload for an `os` field

#### Scenario: Legacy neofetch report rejected
- **WHEN** a client uploads a report identified as `neofetch`
- **THEN** the system rejects it as an unknown report type

### Requirement: Detect fastfetch report by filename

The system SHALL identify a tar member as a fastfetch report when its basename
contains `fastfetch` and ends in `.json`.

#### Scenario: Current client filename
- **WHEN** a tar archive contains `output-lobos-wtoorren-15-09-2026/fastfetch.json`
- **THEN** the member is detected as report type `fastfetch`

#### Scenario: Legacy client filename not detected
- **WHEN** a tar archive contains `neofetch.json`
- **THEN** the member is not detected as any report type and is not stored as
  system information

#### Scenario: Non-JSON system info not detected
- **WHEN** a tar archive contains `neofetch.txt` or `fastfetch.txt`
- **THEN** the member is not detected as any report type

### Requirement: Pass OS type to cache

The system SHALL pass extracted OS type to compliance cache when updating system metadata.

#### Scenario: Cache receives extracted OS type
- **WHEN** a fastfetch upload completes with extracted os_type "Ubuntu 22.04"
- **THEN** compliance cache is updated with os_type "Ubuntu 22.04"

#### Scenario: Cache update enables immediate dashboard refresh
- **WHEN** a fastfetch upload completes with extracted os_type
- **THEN** dashboard refresh shows updated OS type without server restart
