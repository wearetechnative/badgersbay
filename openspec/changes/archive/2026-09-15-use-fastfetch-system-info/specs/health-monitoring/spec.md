## MODIFIED Requirements

### Requirement: Reports by Type Statistics

The health endpoint SHALL return counts of each supported report type found in
storage, using `fastfetch` as the system information report type.

```json
{
  "statistics": {
    "reports_by_type": {
      "lynis": 40,
      "fastfetch": 38
    }
  }
}
```

#### Scenario: Report type counting
- **WHEN** the health endpoint is requested
- **THEN** the response includes counts for:
  - `lynis`: number of directories containing `lynis-report.json`
  - `fastfetch`: number of directories containing `fastfetch-report.json`

#### Scenario: Zero reports of a type
- **WHEN** no directories contain a specific report type
- **THEN** that report type's count is 0 in the response

#### Scenario: Legacy neofetch files not counted
- **WHEN** a directory contains `neofetch-report.json` from an earlier client
  generation
- **THEN** it does not contribute to any report type count, and no `neofetch`
  key appears in `reports_by_type`

**Note:** One directory can contribute to multiple report type counts.
