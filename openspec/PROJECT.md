# Honeybadger Server - Project Overview

## Purpose

Centralized security report aggregation for infrastructure monitoring. Collects scan results from multiple hosts and provides a unified dashboard for compliance and vulnerability tracking.

## Capabilities

The server provides four core capabilities:

### 1. Report Ingestion
**Spec:** [`specs/report-ingestion/spec.md`](specs/report-ingestion/spec.md)

HTTP API for receiving security scan reports from remote hosts. Validates report type, structure, and JSON format before accepting.

**Key features:**
- Dual input methods (headers or JSON body)
- Type-specific validation (Lynis, Trivy, Vulnix, Neofetch)
- Fail-fast with clear error messages

### 2. Report Storage
**Spec:** [`specs/report-storage/spec.md`](specs/report-storage/spec.md)

Filesystem-based storage organized by hostname, username, and date. No database required.

**Key features:**
- Date-organized directory structure
- Same-day overwrites (allows re-scans)
- Path traversal protection

### 3. Status Dashboard
**Spec:** [`specs/status-dashboard/spec.md`](specs/status-dashboard/spec.md)

Web UI for viewing all collected reports with filtering, sorting, and download capabilities.

**Key features:**
- Real-time filtering
- Status indicators (OK/NOK)
- Auto-refresh every 30s
- Report download links

### 4. Health Monitoring
**Spec:** [`specs/health-monitoring/spec.md`](specs/health-monitoring/spec.md)

Machine-readable health check endpoint for monitoring system integration.

**Key features:**
- JSON status response
- Server statistics
- Uptime tracking
- Storage accessibility check

## Technology Stack

- **Language:** Python 3
- **Framework:** Standard library `http.server`
- **Dependencies:** PyYAML (config parsing only)
- **Storage:** Filesystem (JSON files)
- **Frontend:** Embedded HTML/CSS/JS (no build step)

## System Boundaries

```
┌───────────────────────────────────────────────────────┐
│                  IN SCOPE                             │
├───────────────────────────────────────────────────────┤
│ ✓ Receive reports via HTTP POST                      │
│ ✓ Validate report structure                          │
│ ✓ Store reports on filesystem                        │
│ ✓ Display reports in web dashboard                   │
│ ✓ Health check for monitoring                        │
│ ✓ Report download                                    │
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│                 OUT OF SCOPE                          │
├───────────────────────────────────────────────────────┤
│ ✗ Running the scans (Lynis, Trivy, etc.)            │
│ ✗ Scheduling scans on client systems                │
│ ✗ Authentication/authorization                       │
│ ✗ TLS/HTTPS termination                             │
│ ✗ Report analysis/recommendations                   │
│ ✗ Alerting/notifications                            │
│ ✗ Historical trending                               │
│ ✗ Report retention/cleanup                          │
└───────────────────────────────────────────────────────┘
```

## Architecture Principles

1. **Simplicity over features** - Single-file deployment, minimal dependencies
2. **Filesystem as database** - No DB setup required, easy backups
3. **Stateless design** - No sessions, no in-memory state (except uptime)
4. **Fail-fast validation** - Reject invalid data immediately
5. **Self-contained UI** - No build process, no external assets

## Development Workflow

### Making Changes

1. **Explore ideas** - Use `/opsx:explore` to think through changes
2. **Propose changes** - Use `/opsx:propose` to create structured change proposal
3. **Review proposal** - Check generated proposal, design, specs, tasks
4. **Implement** - Use `/opsx:apply` to work through tasks
5. **Archive** - Use `/opsx:archive` when change is complete

### Specs as Documentation

Each capability has a spec that documents:
- Current behavior (the spec IS the documentation)
- HTTP APIs with examples
- Validation rules
- File formats
- Implementation locations (line numbers)
- Known limitations
- Future considerations

**Update specs when behavior changes!**

## Common Change Patterns

### Adding a New Report Type

**Example:** Add support for ClamAV virus scan reports

**Affected capabilities:**
- Report Ingestion (add validation)
- Report Storage (add filename mapping)
- Status Dashboard (add badge display)
- Health Monitoring (add to statistics)

**Steps:**
1. Propose change with `/opsx:propose`
2. Update `report-ingestion/spec.md` with new validation rules
3. Implement validation, storage, display
4. Test with sample ClamAV report
5. Archive change

### Changing Dashboard UI

**Example:** Add sort-by-date functionality

**Affected capabilities:**
- Status Dashboard (modify HTML/JS)

**Steps:**
1. Explore UX options in explore mode
2. Propose change
3. Update `status-dashboard/spec.md`
4. Modify `generate_status_html()` function
5. Test with various report sets
6. Archive change

### Improving Validation

**Example:** Stricter Trivy report validation

**Affected capabilities:**
- Report Ingestion (modify validation logic)

**Steps:**
1. Document new validation rules in proposal
2. Update `report-ingestion/spec.md`
3. Modify `validate_report_structure()`
4. Test with valid and invalid reports
5. Archive change

## Testing Strategy

### Manual Testing

```bash
# Start server
./honeybadger_server.py

# Submit test reports
./test.sh

# Verify dashboard
curl http://localhost:7123/ | grep "testhost"

# Check health
curl http://localhost:7123/health | jq .status
```

### Test Files

- `test-lynis-report.json` - Sample Lynis output
- `test-trivy-report.json` - Sample Trivy output
- `test.sh` - Automated submission script

### Validation Testing

Test each report type with:
- Valid report (should accept)
- Missing required fields (should reject with clear error)
- Invalid JSON (should reject)
- Wrong report type (should reject)

## Deployment Context

**Typical environment:**
- Internal infrastructure network
- Behind firewall (no public internet access)
- Runs on dedicated monitoring/management server
- Clients POST from cron jobs

**Expected scale:**
- 10-100 hosts
- 1-4 reports per host per day
- Low request volume (<10 req/min)

**If you need more:**
- \>100 hosts: Consider database backend
- Public internet: Add authentication + TLS
- High volume: Consider async worker architecture

## Questions?

See [`CLAUDE.md`](../CLAUDE.md) for more detailed technical context.

Check individual capability specs in `specs/` for implementation details.
