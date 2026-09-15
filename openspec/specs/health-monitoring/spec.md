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

### Requirement: Directory and host statistics

The endpoint SHALL report the number of report directories and the number of
distinct hostnames derived from them.

#### Scenario: Total report directories
- **WHEN** health is requested
- **THEN** `statistics.total_report_directories` is the count of subdirectories
  in the configured storage location

#### Scenario: Unique hosts
- **WHEN** directory names follow `<hostname>-<username>-<yyyymmdd>`
- **THEN** `statistics.unique_hosts` is the count of distinct hostnames parsed
  from them

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
