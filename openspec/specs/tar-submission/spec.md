# Tar Submission

## Purpose
Defines how the server accepts a bundled submission at `POST /submit-tar`:
what it stores, which members it extracts as reports, how it reports the
outcome per member, and the limits an archive must stay within.

## Requirements

### Requirement: Accept and store a tar archive

The server SHALL accept a tar or tar.gz archive at `POST /submit-tar` and SHALL
store the archive whole, unchanged, regardless of what it extracts from it.

#### Scenario: Archive stored byte-identical
- **WHEN** a client submits an archive
- **THEN** the stored file is byte-identical to what was sent, because the
  archive is the evidence of record

#### Scenario: Required headers
- **WHEN** a submission omits `X-Hostname` or `X-Username`
- **THEN** the server responds 400 and stores nothing

#### Scenario: Not a tar archive
- **WHEN** the body cannot be opened as a tar archive
- **THEN** the server responds 400 and stores nothing

#### Scenario: Multiple submissions in one period
- **WHEN** a system submits twice within the same audit period
- **THEN** both archives are kept, distinguished by an upload timestamp in the
  filename

### Requirement: Extract recognised reports from the archive

The server SHALL extract JSON members whose report type it recognises and SHALL
store each through the normal report storage path, alongside the archive. It
SHALL also extract the asset inventory, which is a summary of those reports
rather than a report itself.

#### Scenario: Reports extracted and stored
- **WHEN** an archive contains `fastfetch.json` and `lynis-report.json`
- **THEN** both are stored as `fastfetch-report.json` and `lynis-report.json`
  in the same directory as the archive

#### Scenario: Asset inventory extracted
- **WHEN** an archive contains `asset-inventory.json`
- **THEN** it is stored in the submission record and is not reported as an
  unrecognised member

#### Scenario: The inventory is not a report type
- **WHEN** an archive carries an asset inventory
- **THEN** it does not contribute to completeness, and its absence is not a
  missing requirement

#### Scenario: Completeness reflects contents
- **WHEN** an archive containing a complete report set is submitted
- **THEN** the system is recorded complete, rather than recorded as holding
  only an archive

#### Scenario: Non-JSON members ignored
- **WHEN** an archive contains `hardware-serial.txt`, `asset-inventory.txt` or
  other non-JSON members
- **THEN** they are left in the stored archive and not extracted

#### Scenario: Previously stored archives unaffected
- **WHEN** archives stored before this behaviour existed are present on disk
- **THEN** they are not re-processed, and the periods holding them keep their
  recorded figures

### Requirement: Report per-file status

The server SHALL report the outcome per member and SHALL NOT reject an archive
because a single member is unrecognised.

#### Scenario: All members recognised
- **WHEN** every JSON member has a recognised report type
- **THEN** the server responds 200 with the list of stored reports

#### Scenario: Some members unrecognised
- **WHEN** an archive contains `fastfetch.json` and an unrecognised JSON member
- **THEN** the server responds 207 Multi-Status, stores the recognised report,
  names the unrecognised member, and stores the archive

#### Scenario: No recognised members
- **WHEN** no JSON member has a recognised report type
- **THEN** the server responds 207, stores the archive, and the system is
  recorded incomplete

#### Scenario: Legacy neofetch member
- **WHEN** an archive contains `neofetch.json` from an earlier client
- **THEN** it is reported as unrecognised rather than stored as system
  information

### Requirement: Determine OS type from the archive

The server SHALL take the OS type from the extracted fastfetch report, using
the `X-OS-Type` header only when the archive carries no fastfetch member.

#### Scenario: OS type from the archive
- **WHEN** an archive contains `fastfetch.json` with an `os` field
- **THEN** that value is recorded as the system's OS type, whatever the
  `X-OS-Type` header says

#### Scenario: Fallback to the header
- **WHEN** an archive has no fastfetch member and `X-OS-Type` is supplied
- **THEN** the header value is recorded

#### Scenario: Neither available
- **WHEN** an archive has no fastfetch member and no `X-OS-Type` header
- **THEN** the OS type is recorded as "unknown"

### Requirement: Enforce archive limits

The server SHALL reject an archive that exceeds its size, count or path limits
before extracting anything from it.

#### Scenario: Archive too large
- **WHEN** the submitted archive exceeds 50MB
- **THEN** the server responds 413 and stores nothing

#### Scenario: Member too large
- **WHEN** a member exceeds 10MB
- **THEN** the server responds 400 and stores nothing

#### Scenario: Too many members
- **WHEN** an archive holds more than 100 members
- **THEN** the server responds 400 and stores nothing

#### Scenario: Unsafe member path
- **WHEN** a member has an absolute path, a parent-directory reference, a
  symlink, or nesting deeper than three levels
- **THEN** the server responds 400 and stores nothing
