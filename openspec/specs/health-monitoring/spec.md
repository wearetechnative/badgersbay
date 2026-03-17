# Health Monitoring

## Overview

Machine-readable health check endpoint providing server status, uptime, and statistics. Designed for integration with monitoring systems (Prometheus, Nagios, etc.).

## Endpoint

```
GET /health
Content-Type: application/json
```

## Response Format

### Success Response (HTTP 200)

```json
{
  "status": "ok",
  "http_code": 200,
  "service": "honeybadger-server",
  "timestamp": "2026-03-16T14:30:00.123456",
  "uptime": {
    "seconds": 3600,
    "human_readable": "1h 0m"
  },
  "statistics": {
    "total_report_directories": 42,
    "unique_hosts": 15,
    "reports_by_type": {
      "lynis": 40,
      "trivy": 35,
      "vulnix": 20,
      "neofetch": 38
    }
  },
  "storage": {
    "location": "./reports",
    "accessible": true
  }
}
```

### Error Response (HTTP 500)

```json
{
  "status": "error",
  "http_code": 500,
  "service": "honeybadger-server",
  "error": "Error message details"
}
```

## Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `"ok"` or `"error"` |
| `http_code` | integer | HTTP status code (200, 500) |
| `service` | string | Always `"honeybadger-server"` |
| `timestamp` | string | Current server time (ISO 8601 format) |
| `uptime.seconds` | integer | Server uptime in seconds |
| `uptime.human_readable` | string | Format: `"<hours>h <minutes>m"` |
| `statistics.total_report_directories` | integer | Count of report directories |
| `statistics.unique_hosts` | integer | Count of distinct hostnames |
| `statistics.reports_by_type` | object | Count of each report type found |
| `storage.location` | string | Configured storage path |
| `storage.accessible` | boolean | Whether storage directory exists |

## Statistics Calculation

### Total Report Directories

Count of all subdirectories in `storage_location`.

### Unique Hosts

Distinct hostnames extracted from directory names (`<hostname>-<username>-<yyyymmdd>`).

**Parsing logic:**
```
Directory: webserver01-admin-20260316
           └─────┬─────┘ └──┬─┘ └───┬───┘
              hostname    user    date
```

### Reports by Type

For each report directory, check file existence:
- `lynis-report.json` exists → increment `reports_by_type.lynis`
- `trivy-report.json` exists → increment `reports_by_type.trivy`
- `vulnix-report.json` exists → increment `reports_by_type.vulnix`
- `neofetch-report.json` exists → increment `reports_by_type.neofetch`

**Note:** One directory can contribute to multiple report type counts.

### Storage Accessible

Checks if `Path(storage_location).exists()` returns true.

## Uptime Tracking

**Start time:** Recorded in `ReportHandler.start_time` when server starts.

**Calculation:**
```python
uptime_seconds = current_time - start_time
uptime_hours = uptime_seconds // 3600
uptime_minutes = (uptime_seconds % 3600) // 60
```

**Note:** Uptime resets on server restart (no persistence).

## Use Cases

### Monitoring Systems

**Prometheus:**
```yaml
scrape_configs:
  - job_name: 'honeybadger'
    static_configs:
      - targets: ['localhost:7123']
    metrics_path: '/health'
```

**Nagios/Icinga:**
```bash
check_http -H localhost -p 7123 -u /health -s '"status":"ok"'
```

### Healthcheck Scripts

```bash
#!/bin/bash
response=$(curl -s http://localhost:7123/health)
status=$(echo "$response" | jq -r '.status')

if [ "$status" = "ok" ]; then
  echo "OK - Honeybadger server is healthy"
  exit 0
else
  echo "CRITICAL - Honeybadger server error"
  exit 2
fi
```

### Container Orchestration

**Docker Compose:**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:7123/health"]
  interval: 30s
  timeout: 5s
  retries: 3
```

**Kubernetes:**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 7123
  initialDelaySeconds: 10
  periodSeconds: 30
```

## Implementation Location

- Handler: `honeybadger_server.py:do_GET()` (line 732)
- Status generation: `get_health_status()` (line 104)
- Start time init: `run_server()` (line 799)

## Performance

- **Response time:** ~5-50ms depending on report count
- **No caching:** Stats calculated on every request
- **I/O operations:** Scans filesystem on each call

## Limitations

- No authentication (publicly accessible)
- No detailed error diagnostics
- No historical metrics
- Uptime not persisted across restarts
- No alerting thresholds

## Future Enhancements

- Prometheus-native `/metrics` endpoint
- Configurable alert thresholds
- Historical uptime tracking
- Detailed error states (disk full, permissions, etc.)
- Response time percentiles
- Authentication/API keys
