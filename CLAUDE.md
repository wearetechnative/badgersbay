# Honeybadger Server - AI Context

This document provides context for AI assistants working on this project.

## What This Is

A **centralized security report aggregation server** that collects vulnerability scan results from multiple hosts and displays them in a unified dashboard.

Think of it as a "security scan inbox" - clients run scans (Lynis) and POST their results here along with system information (Neofetch). Sysadmins visit the dashboard to see the security posture of all their systems at a glance.

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
│  Neofetch ─┼───┼── POST ───▶│   │Validation│   │
│            │   │            │   └────┬─────┘   │
│            │   │            │        │         │
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
| **Trivy** | Container and OS vulnerability scanner | All (containers/traditional) |
| **Vulnix** | NixOS-specific vulnerability scanner | NixOS systems |
| **Neofetch** | System metadata/identity | All (required!) |

### The "OK" Logic

A system is marked **OK** (green) if it has:
- **Neofetch** (always required - provides system identity)
- **AND** Lynis (system audit - always needed)
- **AND** Trivy or Vulnix (vulnerability scanner - at least one)

**Rationale:** For ISO compliance, systems need baseline hardening audit (Lynis), identity (Neofetch), and vulnerability scanning (Trivy or Vulnix depending on OS).

## File Locations

```
honeybadger-server/
├── honeybadger_server.py    # Everything is here
├── config.yaml              # Port + storage path
├── requirements.txt         # Just PyYAML
├── README.md               # User documentation
├── CLAUDE.md               # This file
├── BUGFIXES.md             # Documented bug fixes
├── test.sh                 # Quick test script (single reports)
├── test-tar-submit.sh      # Test script for tar submission
├── test-*.json             # Sample reports
├── example-client-submit-tar.sh  # Example client for tar submission
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

## CLI Arguments and Config Loading

The server supports flexible configuration file location via CLI arguments:

**Arguments:**
- `--config PATH`: Specify custom config file location
- `--version`: Display version information
- `--help`: Show usage information

**Config File Search Order (when --config not provided):**
1. Current working directory (`./config.yaml`)
2. Script directory (same directory as honeybadger_server.py)
3. System location (`/etc/honeybadger/config.yaml`)

**Implementation:**
- `parse_arguments()`: Argparse-based CLI parsing
- `find_config_file(cli_config_path)`: Config discovery with fallback chain
- `main()`: Integrates argument parsing before config loading

**Use cases:**
- **Per-instance configs**: Run from different directories with their own config.yaml
- **System-wide install**: Script in /usr/local/bin/, config in /etc/honeybadger/
- **Containerized**: Volume-mount config at custom location with --config
- **Backward compatible**: No CLI args = searches script directory (legacy behavior)

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

## Endpoints

The server provides two methods for report submission:

### 1. Single Report Submission (POST /)
Traditional endpoint for submitting one report at a time:
- Client sends X-Hostname, X-Username, X-Report-Type headers
- Body contains JSON report data
- One HTTP request per report type

### 2. Tar Archive Submission (POST /submit-tar)
New endpoint for submitting multiple reports at once:
- Client sends X-Hostname, X-Username headers
- Body contains tar/tar.gz archive with multiple JSON files
- Filename-based report type detection (lynis.json, neofetch-report.json, etc.)
- Returns detailed per-file status (HTTP 200/207/400)
- Security: validates paths, enforces size limits (50MB tar, 10MB per file, max 100 files)

**Advantages of tar submission:**
- Reduces network round-trips (4 reports = 1 request vs 4 requests)
- Simplifies client scripts (bundle once, upload once)
- Atomic: all reports for same audit period
- Better for unreliable networks

## Testing

```bash
# Quick test with sample data (single reports)
./test.sh

# Test tar submission feature
./test-tar-submit.sh

# Manual test - single report
curl -X POST http://localhost:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: testhost" \
  -H "X-Username: testuser" \
  -H "X-Report-Type: lynis" \
  -d @test-lynis-report.json

# Manual test - tar submission
tar -czf reports.tar.gz test-lynis-report.json test-neofetch-report.json
curl -X POST http://localhost:7123/submit-tar \
  -H "X-Hostname: testhost" \
  -H "X-Username: testuser" \
  --data-binary @reports.tar.gz

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

## Git Commit Guidelines

**IMPORTANT:** Never mention AI assistance in commit messages:
- **DO NOT** add "Co-Authored-By: Claude" or similar attributions
- **DO NOT** mention "AI-generated", "AI-assisted", or "Claude" anywhere in commit messages
- Commit messages should reflect the technical changes only
- Keep commits professional and focused on the work itself
