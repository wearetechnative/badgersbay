# Health Monitoring

## Purpose
Defines the unauthenticated `/health` endpoint: its response contract, the
statistics it reports, and how uptime and storage accessibility are determined.
The endpoint is consumed by monitoring systems and container orchestration, so
its field names and shapes are a contract rather than documentation.

## Requirements

### Requirement: Health endpoint is unauthenticated

The server SHALL serve `GET /health` without authentication and SHALL return
`application/json`.

#### Scenario: No credentials supplied
- **WHEN** `GET /health` is requested without an Authorization header
- **THEN** the server responds normally rather than with 401

#### Scenario: Content type
- **WHEN** `GET /health` is requested
- **THEN** the response `Content-Type` is `application/json`

### Requirement: Success response structure

A healthy server SHALL respond with HTTP 200 and a body containing `status`,
`http_code`, `service`, `timestamp`, `uptime`, `statistics` and `storage`.

#### Scenario: Healthy response fields
- **WHEN** the server is healthy and `GET /health` is requested
- **THEN** the response is HTTP 200 with:
  - `status` = `"ok"`
  - `http_code` = `200`
  - `service` = `"honeybadger-server"`
  - `timestamp` as an ISO 8601 server time
  - `uptime.seconds` as an integer and `uptime.human_readable` as `"<hours>h <minutes>m"`
  - `statistics.total_report_directories`, `statistics.unique_hosts`,
    `statistics.reports_by_type`
  - `storage.location` and `storage.accessible`

#### Scenario: Field names are a contract
- **WHEN** the response shape changes
- **THEN** it is treated as a breaking change for monitoring consumers

### Requirement: Error response structure

A server that cannot report its health SHALL respond with HTTP 500 and a body
containing `status`, `http_code`, `service` and `error`.

#### Scenario: Failure response fields
- **WHEN** health collection fails
- **THEN** the response is HTTP 500 with `status` = `"error"`,
  `http_code` = `500`, `service` = `"honeybadger-server"` and `error` holding
  the failure detail

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

### Requirement: Uptime tracking

The endpoint SHALL report uptime measured from server start, without
persistence across restarts.

#### Scenario: Uptime reported
- **WHEN** the server has been running for one hour
- **THEN** `uptime.seconds` is approximately 3600 and `uptime.human_readable`
  is `"1h 0m"`

#### Scenario: Uptime resets on restart
- **WHEN** the server restarts
- **THEN** uptime restarts from zero

### Requirement: Storage accessibility

The endpoint SHALL report whether the configured storage location exists.

#### Scenario: Storage present
- **WHEN** the configured storage location exists
- **THEN** `storage.accessible` is true and `storage.location` is the
  configured path

#### Scenario: Storage missing
- **WHEN** the configured storage location does not exist
- **THEN** `storage.accessible` is false
