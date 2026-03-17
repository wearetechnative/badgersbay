# Honeybadger Server - AI Context

This document provides context for AI assistants working on this project.

## What This Is

A **centralized security report aggregation server** that collects vulnerability scan results from multiple hosts and displays them in a unified dashboard.

Think of it as a "security scan inbox" - clients run scans (Lynis, Trivy, Vulnix) and POST their results here. Sysadmins visit the dashboard to see the security posture of all their systems at a glance.

## Architecture Philosophy

```
┌─────────────────────────────────────────────┐
│  Design Principle: KISS (Keep It Simple)   │
├─────────────────────────────────────────────┤
│                                             │
│  ✓ Single Python file                      │
│  ✓ No database (filesystem storage)        │
│  ✓ Minimal dependencies (stdlib + PyYAML)  │
│  ✓ Self-contained HTML (no build step)     │
│  ✓ Stateless HTTP server                   │
│  ✓ Deploy = copy one file                  │
│                                             │
└─────────────────────────────────────────────┘
```

**Why?** Meant to run on internal infrastructure servers where simplicity and reliability trump features.

## Domain Model

```
Host System                    Honeybadger Server
┌────────────┐                ┌──────────────────┐
│            │                │                  │
│  Lynis ────┼───┐            │   ┌──────────┐   │
│  Trivy ────┼───┼── POST ───▶│   │Validation│   │
│  Vulnix ───┼───┤            │   └────┬─────┘   │
│  Neofetch ─┼───┘            │        │         │
│            │                │        ▼         │
└────────────┘                │   ┌──────────┐   │
                              │   │ Storage  │   │
                              │   └──────────┘   │
                              │                  │
Sysadmin Browser              │   ┌──────────┐   │
┌────────────┐                │   │Dashboard │   │
│            │◀────GET /──────│   │          │   │
│ 🖥️ Dashboard│                │   └──────────┘   │
└────────────┘                └──────────────────┘
```

### Report Types

| Type | Purpose | Target Systems |
|------|---------|----------------|
| **Lynis** | System hardening audit | All Linux/Unix |
| **Trivy** | Container/OS vulnerabilities | Docker/Kubernetes hosts |
| **Vulnix** | NixOS-specific vulnerabilities | NixOS systems |
| **Neofetch** | System metadata/identity | All (required!) |

### The "OK" Logic

A system is marked **OK** (green) if it has:
- **Neofetch** (always required - provides system identity)
- **AND** Lynis (system audit - always needed)
- **AND** Either:
  - Trivy (for container/traditional systems)
  - **OR** Vulnix (for NixOS)

**Rationale:** Different systems need different scanners, but all need baseline hardening (Lynis) and identity (Neofetch).

## File Locations

```
honeybadger-server/
├── honeybadger_server.py    # Everything is here
├── config.yaml              # Port + storage path
├── requirements.txt         # Just PyYAML
├── README.md               # User documentation
├── CLAUDE.md               # This file
├── BUGFIXES.md             # Documented bug fixes
├── test.sh                 # Quick test script
├── test-*.json             # Sample reports
└── openspec/               # Change management
    ├── config.yaml         # Project context
    ├── specs/              # Capability specifications
    │   ├── report-ingestion/
    │   ├── report-storage/
    │   ├── status-dashboard/
    │   └── health-monitoring/
    └── changes/            # Active changes
```

## Code Structure

The single Python file is organized as:

| Lines | Purpose |
|-------|---------|
| 1-46 | Config loading (YAML) |
| 49-103 | Validation logic |
| 104-158 | Health check endpoint |
| 160-223 | POST handler (receive reports) |
| 224-257 | Storage logic |
| 259-330 | Report scanning (for dashboard) |
| 332-721 | HTML dashboard generation |
| 723-792 | GET handler (dashboard + health + downloads) |
| 795-837 | Server startup |

**Key pattern:** No classes except `Config` and `ReportHandler`. Pure functions for logic.

## Storage Layout

```
./reports/
  └── <hostname>-<username>-<yyyymmdd>/
      ├── lynis-report.json
      ├── trivy-report.json
      ├── vulnix-report.json
      └── neofetch-report.json
```

**Example:** `webserver01-admin-20260316/`

**Overwrite behavior:** Same-day reports overwrite. Different dates create new directories.

## Common Tasks

### Adding a new report type

1. Add to `valid_types` list (line 61)
2. Add validation logic in `validate_report_structure()` (line 66)
3. Add filename mapping in `save_report()` (line 236)
4. Update dashboard HTML generation (line 332)
5. Update status logic if required for "OK" (line 645)

### Changing validation rules

1. Modify `validate_report_structure()` (line 66)
2. Update corresponding spec in `openspec/specs/<type>/spec.md`
3. Test with sample reports

### Modifying dashboard

1. Edit HTML template in `generate_status_html()` (line 332)
2. CSS is inline at line 342
3. JavaScript is inline at line 545

## Testing

```bash
# Quick test with sample data
./test.sh

# Manual test
curl -X POST http://localhost:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: testhost" \
  -H "X-Username: testuser" \
  -H "X-Report-Type: lynis" \
  -d @test-lynis-report.json

# Check dashboard
open http://localhost:7123/

# Check health
curl http://localhost:7123/health | jq
```

## Deployment

```bash
# Server (where reports are aggregated)
pip install -r requirements.txt
./honeybadger_server.py

# Clients (systems being scanned)
# Add to cron: run scan, POST to server
0 3 * * * /path/to/scan-and-submit.sh
```

## Current Limitations

- **No authentication** - Anyone on network can POST/view
- **No TLS** - Plain HTTP only
- **No rate limiting** - Can be flooded
- **No retention policy** - Reports accumulate forever
- **No database** - Filesystem only (slow with thousands of reports)
- **No pagination** - Dashboard loads all reports at once
- **Single threaded** - Python http.server limitation

These are **by design** for simplicity. If you need these, consider if the project is growing beyond its intended use case.

## When to Refactor

Consider splitting into multiple files if:
- Adding >2 new report types
- Adding authentication system
- Adding database backend
- Adding API versioning
- Team size > 2 developers

Otherwise, maintain single-file simplicity.

## Related Projects

This is part of the `toortools` suite:
- Location: `/home/wtoorren/data/git/wearetechnative/toortools/`
- Sibling: `hb-v2/` (possible next version?)

## Questions to Ask

When proposing changes, consider:

1. **Does this maintain single-file deployment?**
2. **Does this add external dependencies?**
3. **Is this needed for the core use case (internal infrastructure)?**
4. **Could this be a separate tool instead?**
5. **Does this break backwards compatibility with existing clients?**

## Getting Help

- Issues: https://github.com/wearetechnative/toortools (if public)
- Specs: See `openspec/specs/` for detailed capability docs
- Bugfixes: See `BUGFIXES.md` for documented bug fixes and their resolutions
- Code: Read `honeybadger_server.py` - it's only 837 lines!
