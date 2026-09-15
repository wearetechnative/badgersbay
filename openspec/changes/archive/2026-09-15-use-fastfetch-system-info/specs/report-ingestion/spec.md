## REMOVED Requirements

### Requirement: Extract OS type from neofetch JSON data

**Reason**: The client migrated from neofetch to fastfetch and emits
`fastfetch.json`. A requirement named after the retired tool cannot describe
the system information the server now receives.

**Migration**: Replaced by "Extract OS type from fastfetch JSON data" below.
Existing `neofetch-report.json` files stay on disk as archive; they are no
longer read as system information.

## ADDED Requirements

### Requirement: Extract OS type from fastfetch JSON data

The system SHALL extract the OS type from the `os` field of an uploaded
fastfetch report and pass it to the compliance cache.

#### Scenario: OS type present in fastfetch report
- **WHEN** a client uploads `fastfetch.json` containing `{"os": "NixOS 26.05 (Yarara)"}`
- **THEN** the system records OS type "NixOS 26.05 (Yarara)" for that system

#### Scenario: OS field absent
- **WHEN** an uploaded fastfetch report has no `os` field
- **THEN** the system records OS type "unknown" and accepts the report

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
