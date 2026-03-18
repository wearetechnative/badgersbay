## MODIFIED Requirements

### Requirement: Reports by Type Statistics

The health endpoint SHALL return counts of each supported report type found in storage.

```json
{
  "statistics": {
    "reports_by_type": {
      "lynis": 40,
      "neofetch": 38
    }
  }
}
```

#### Scenario: Report type counting
- **WHEN** health endpoint is requested
- **THEN** response includes counts for:
  - `lynis`: number of directories containing `lynis-report.json`
  - `neofetch`: number of directories containing `neofetch-report.json`

#### Scenario: Zero reports of a type
- **WHEN** no directories contain a specific report type
- **THEN** that report type's count is 0 in the response

## REMOVED Requirements

### Requirement: Trivy report counting
**Reason**: Trivy report type is no longer supported
**Migration**: Remove `trivy` key from `reports_by_type` object in health endpoint response. Monitoring systems should update their metrics collection to no longer expect this field.

### Requirement: Vulnix report counting
**Reason**: Vulnix report type is no longer supported
**Migration**: Remove `vulnix` key from `reports_by_type` object in health endpoint response. Monitoring systems should update their metrics collection to no longer expect this field.
