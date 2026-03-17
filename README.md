[](images/badgersbay-github.png)

# Honeybadger Server

A central server for collecting and storing Lynis, Trivy, Vulnix, and Neofetch (system info) reports with built-in ISO compliance tracking.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
./honeybadger_server.py
```

**Compliance dashboard:** Open `http://localhost:7123/` in your browser

The server runs in **compliance mode** by default (see `config.yaml`), tracking endpoint audits for ISO requirements. To use legacy mode instead, set `compliance.enabled: false` in the config.

## Configuration

Edit `config.yaml`:

```yaml
networkport: 7123           # Port the server listens on
storage_location: ./reports # Directory where reports are stored

# Compliance mode is ENABLED by default
compliance:
  enabled: true
  audit_months: [3, 9]      # March and September audits
  required_reports:
    mandatory:
      - neofetch
      - lynis
    one_of:
      - trivy
      - vulnix
```

## Compliance Mode (ISO Audit Tracking)

Honeybadger supports compliance tracking for periodic audits (e.g., ISO requirements for 2x yearly endpoint audits).

### Enabling Compliance Mode

Add to `config.yaml`:

```yaml
compliance:
  enabled: true

  # Audit months (when compliance audits must be completed)
  audit_months: [3, 9]  # March and September

  # Required reports for a complete set
  required_reports:
    mandatory:
      - neofetch  # System identification (always required)
      - lynis     # Security audit (always required)
    one_of:
      - trivy     # Container/OS scanner (Ubuntu, Debian, etc.)
      - vulnix    # NixOS scanner
```

### How It Works

**Audit Period Mapping:**
- Uploads automatically map to the next audit month
- Example with `audit_months: [3, 9]`:
  - January/February upload → March 2026 period
  - April-August upload → September 2026 period
  - October-February upload → March 2027 period

**Storage Structure:**
```
./reports/
  ├── 2026-03/           ← Audit period (March 2026)
  │   ├── laptop-SN001-alice/
  │   │   ├── neofetch-report.json
  │   │   ├── lynis-report.json
  │   │   └── trivy-report.json
  │   └── laptop-SN002-bob/
  │       └── ...
  └── 2026-09/           ← Audit period (September 2026)
      └── ...
```

**Report Completeness:**

A system is **compliant** when it has:
- ✓ Neofetch report (provides system ID)
- ✓ Lynis report (security audit)
- ✓ **Either** Trivy **OR** Vulnix (at least one scanner)

**Compliance Dashboard:**

Open `http://localhost:7123/` to view:
- Audit period selector
- Summary statistics (total, complete, incomplete, compliance %)
- System table with compliance status
- Filter by complete/incomplete
- Download individual reports

### Client Integration (Optional X-OS-Type Header)

Clients can optionally send OS type for better tracking:

```bash
curl -X POST http://server:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-OS-Type: ubuntu" \    # ← Optional
  -H "X-Report-Type: lynis" \
  -d @lynis-report.json
```

Supported values: `ubuntu`, `debian`, `nixos`, `arch`, etc.

### Migration from Legacy Mode

**Existing deployments:**
1. Existing reports in legacy format (`hostname-username-YYYYMMDD/`) remain accessible
2. New uploads after enabling compliance mode use new format (`YYYY-MM/sid-username/`)
3. Legacy reports won't appear in compliance dashboard
4. To view legacy reports: temporarily set `compliance.enabled: false`

**Known Limitations:**
- No automatic migration of legacy reports to compliance structure
- Old and new reports coexist in same `./reports/` directory
- Compliance dashboard only shows reports uploaded in compliance mode

## Submitting Reports

### Option 1: Via HTTP Headers (Recommended)

```bash
# Lynis report
curl -X POST http://server:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-OS-Type: ubuntu" \
  -H "X-Report-Type: lynis" \
  -d @/path/to/lynis-report.json

# Trivy report
curl -X POST http://server:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-OS-Type: ubuntu" \
  -H "X-Report-Type: trivy" \
  -d @/path/to/trivy-report.json
```

### Option 2: Via JSON Body

```bash
curl -X POST http://server:7123/ \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "webserver01",
    "username": "admin",
    "report_type": "lynis",
    "scan_data": {...}
  }'
```

### Required Fields

- **hostname**: Hostname of the scanned machine (required)
- **username**: User who performed the scan (required)
- **report_type**: Report type - "lynis", "trivy", "vulnix", or "neofetch" (required)

### Validation

The server validates:
- **Report type**: Must be one of: lynis, trivy, vulnix, neofetch
- **JSON structure**:
  - Lynis: checks for version fields (warning only)
  - Trivy: requires `SchemaVersion` and `ArtifactName`
  - Vulnix: must be valid JSON object or array
  - Neofetch: must be JSON object with system info fields
- **JSON format**: Must be valid JSON

Invalid reports are rejected with HTTP 400 and a descriptive error message.

## Integration with Scans

### Lynis

```bash
#!/bin/bash
# Run Lynis scan and submit report
lynis audit system --quick

# Submit report to Honeybadger server
curl -X POST http://honeybadger-server:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-OS-Type: ubuntu" \
  -H "X-Report-Type: lynis" \
  -d @/var/log/lynis-report.json
```

### Trivy

```bash
#!/bin/bash
# Scan container image with Trivy
trivy image --format json --output trivy-report.json ubuntu:22.04

# Submit report to Honeybadger server
curl -X POST http://honeybadger-server:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-OS-Type: ubuntu" \
  -H "X-Report-Type: trivy" \
  -d @trivy-report.json
```

### Vulnix

```bash
#!/bin/bash
# Scan NixOS system with Vulnix
vulnix --json > vulnix-report.json

# Submit report to Honeybadger server
curl -X POST http://honeybadger-server:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-OS-Type: nixos" \
  -H "X-Report-Type: vulnix" \
  -d @vulnix-report.json
```

### Neofetch (System Info)

Since neofetch doesn't support JSON output natively, create a JSON report with system information:

```bash
#!/bin/bash
# Create neofetch-compatible JSON report

cat > neofetch-report.json <<'EOF'
{
  "host": "$(hostname -s)",
  "hostname": "$(hostname)",
  "os": "$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '\"')",
  "kernel": "$(uname -r)",
  "architecture": "$(uname -m)",
  "uptime": "$(uptime -p)",
  "timestamp": "$(date -Iseconds)"
}
EOF

# Expand variables
eval "cat <<EOF
$(cat neofetch-report.json)
EOF
" > neofetch-report.json

# Submit report to Honeybadger server
curl -X POST http://honeybadger-server:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-OS-Type: ubuntu" \
  -H "X-Report-Type: neofetch" \
  -d @neofetch-report.json
```

**Important:** The `host` field in the neofetch report is used for the SID column in the dashboard.

## Status Dashboard

Open `http://localhost:7123/` in your browser. The dashboard automatically switches based on the `compliance.enabled` setting.

### Compliance Dashboard (compliance.enabled: true)

Shows audit-period-based tracking:

- **Audit period selector**: Switch between periods (e.g., 2026-03, 2026-09)
- **Summary statistics**: Total systems, complete, incomplete, compliance percentage
- **System table columns**:
  - **SID**: System ID from neofetch report's `host` field
  - **Username**: User who submitted the report
  - **OS Type**: Operating system (from X-OS-Type header)
  - **Upload Date**: When reports were submitted
  - **Reports**: Badge indicators (N=Neofetch, L=Lynis, T=Trivy, V=Vulnix)
  - **Status**: ✓ Complete, ⚠ Incomplete, ✗ Missing
- **Filter dropdown**: Show all, complete only, or incomplete only
- **Download**: Click report badges to download individual reports

**Completeness criteria** (configurable in `config.yaml`):
- ✓ Complete: Has all mandatory reports + at least one from one_of list
- ⚠ Incomplete: Missing some required reports
- ✗ Missing: No neofetch report (cannot identify system)

### Legacy Dashboard (compliance.enabled: false)

Shows date-based tracking:

- Overview of all received reports grouped by upload date
- **Columns**: Hostname, SID, Username, Report Date, Last Update, Reports, Status
- Filter/search functionality for hostname, SID, username, or date
- Auto-refresh every 30 seconds
- **Status indicators**:
  - **Green OK**: Valid combination (Neofetch + Lynis + Trivy OR Neofetch + Lynis + Vulnix)
  - **Red NOK**: Missing required reports
- Download individual reports by clicking badges

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` or `/status` | GET | HTML status dashboard |
| `/` | POST | Receive a security report |
| `/health` | GET | Health check with monitoring data (JSON) |
| `/reports/<path>` | GET | Download a specific report |

### Health Check Endpoint

The `/health` endpoint returns detailed monitoring information:

```bash
curl http://localhost:7123/health
```

**Response (HTTP 200):**
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
      "vulnix": 20
    }
  },
  "storage": {
    "location": "./reports",
    "accessible": true
  }
}
```

This endpoint is suitable for monitoring systems like Prometheus, Nagios, or custom health checks.

## Storage Structure

The server supports two storage modes based on the `compliance.enabled` setting.

### Compliance Mode (compliance.enabled: true)

Audit-period-based structure:

```
reports/
  ├── 2026-03/                    ← Audit period (March 2026)
  │   ├── laptop-SN001-alice/     ← {sid}-{username}
  │   │   ├── neofetch-report.json
  │   │   ├── lynis-report.json
  │   │   └── trivy-report.json
  │   └── laptop-SN002-bob/
  │       ├── neofetch-report.json
  │       ├── lynis-report.json
  │       └── vulnix-report.json
  └── 2026-09/                    ← Audit period (September 2026)
      └── ...
```

- **Directory naming**: `{audit-period}/{sid}-{username}/`
- **SID extraction**: From neofetch report's `host` field (fallback: hostname)
- **Report naming**: `{report-type}-report.json`

### Legacy Mode (compliance.enabled: false)

Date-based structure:

```
reports/
  ├── webserver01-alice-20260316/  ← {hostname}-{username}-{YYYYMMDD}
  │   ├── lynis-report.json
  │   ├── trivy-report.json
  │   └── neofetch-report.json
  └── laptop42-bob-20260317/
      └── ...
```

- **Directory naming**: `{hostname}-{username}-{YYYYMMDD}/`
- **Report naming**: `{report-type}-report.json`

### Valid Report Combinations

**Complete set (configurable):**
- All mandatory reports (default: Neofetch + Lynis)
- At least one from one_of list (default: Trivy OR Vulnix)

**Example valid combinations:**
- Neofetch + Lynis + Trivy ✓
- Neofetch + Lynis + Vulnix ✓
- Neofetch + Lynis + Trivy + Vulnix ✓

## Testing

```bash
# Test with sample data
./test.sh

# View stored reports
ls -lR reports/
```
