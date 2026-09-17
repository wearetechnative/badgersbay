## MODIFIED Requirements

### Requirement: Reports by Type Statistics

The health endpoint SHALL return the number of submission records holding each
supported report type.

```json
{
  "statistics": {
    "reports_by_type": {
      "lynis": 16,
      "fastfetch": 1
    }
  }
}
```

#### Scenario: Report type counting
- **WHEN** the health endpoint is requested
- **THEN** the response includes counts for:
  - `lynis`: number of records containing `lynis-report.json`
  - `fastfetch`: number of records containing `fastfetch-report.json`

#### Scenario: Counted at the system level
- **WHEN** submissions are stored under a hardware serial
- **THEN** report files are looked for inside the record directory, not inside
  the serial directory that holds the records and not inside a period directory

#### Scenario: Zero reports of a type
- **WHEN** no record contains a specific report type
- **THEN** that report type's count is 0 in the response

#### Scenario: Legacy neofetch files not counted
- **WHEN** a directory contains `neofetch-report.json` from an earlier client
  generation
- **THEN** it does not contribute to any report type count, and no `neofetch`
  key appears in `reports_by_type`

**Note:** One record can contribute to multiple report type counts.

## REMOVED Requirements

### Requirement: Directory and host statistics

**Reason**: The requirement described two storage layouts selected by whether
compliance mode is on, and counted only the one that matched. The server writes
serial-keyed records regardless of that flag, so the layout was never a property
of the mode, and the endpoint reported zero on a server that was receiving
submissions.

**Migration**: Replaced by "Submission statistics", which counts every tree the
server reads and keeps `total_report_directories` and `unique_hosts` reporting
what their names say.

## ADDED Requirements

### Requirement: Submission statistics

The endpoint SHALL count every tree the server reads submissions from, and SHALL
report where those submissions came from.

#### Scenario: Every tree the server reads
- **WHEN** health is requested
- **THEN** records under the serial-keyed tree, records that could not be
  matched, and the period directories kept as archive are all counted; a layout
  the server reads but health does not is a monitor reporting silence on a
  working server

#### Scenario: Total report directories
- **WHEN** health is requested
- **THEN** `statistics.total_report_directories` is the count of submission
  records, not of serials and not of audit periods

#### Scenario: Source breakdown
- **WHEN** health is requested
- **THEN** `statistics.by_source` reports `matched`, `unmatched` and `archived`,
  so a machine that is scanning without being credited to any asset can be
  alerted on

#### Scenario: Unique hosts
- **WHEN** several records belong to the same hostname
- **THEN** `statistics.unique_hosts` counts that hostname once, taken from the
  submission record where it has one rather than parsed from a directory name

#### Scenario: Archive only
- **WHEN** the storage tree holds period directories and nothing else
- **THEN** those records are still counted and attributed to `archived`
