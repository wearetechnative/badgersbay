## MODIFIED Requirements

### Requirement: Directory and host statistics

The endpoint SHALL report the number of system directories and the number of
distinct hostnames derived from them, counted according to the active storage
mode.

#### Scenario: Total report directories
- **WHEN** health is requested
- **THEN** `statistics.total_report_directories` is the count of system
  directories, not of audit periods

#### Scenario: Compliance mode layout
- **WHEN** compliance mode is enabled and reports live under
  `reports/<period>/<hostname-username>/`
- **THEN** systems are counted one level below the period directories, and
  `statistics.unique_hosts` is derived from the `hostname-username` part

#### Scenario: Legacy mode layout
- **WHEN** compliance mode is disabled and directories are named
  `<hostname>-<username>-<yyyymmdd>`
- **THEN** systems are counted at the top level and hostnames parsed from that
  shape

#### Scenario: Unique hosts
- **WHEN** several directories belong to the same hostname
- **THEN** `statistics.unique_hosts` counts that hostname once

### Requirement: Reports by Type Statistics

The health endpoint SHALL return the number of system directories holding each
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
  - `lynis`: number of system directories containing `lynis-report.json`
  - `fastfetch`: number of system directories containing `fastfetch-report.json`

#### Scenario: Counted at the system level
- **WHEN** compliance mode is enabled
- **THEN** report files are looked for inside system directories, not inside
  audit period directories

#### Scenario: Zero reports of a type
- **WHEN** no system directory contains a specific report type
- **THEN** that report type's count is 0 in the response

#### Scenario: Legacy neofetch files not counted
- **WHEN** a directory contains `neofetch-report.json` from an earlier client
  generation
- **THEN** it does not contribute to any report type count, and no `neofetch`
  key appears in `reports_by_type`

**Note:** One directory can contribute to multiple report type counts.
