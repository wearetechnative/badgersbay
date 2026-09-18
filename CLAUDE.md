# Honeybadger Server - AI Context

This document provides context for AI assistants working on this project.

## What This Is

A **centralized security report aggregation server** that collects vulnerability scan results from multiple hosts and displays them in a unified dashboard.

Think of it as a "security scan inbox" - clients run scans (Lynis) and POST their results here along with system information (Fastfetch). Sysadmins visit the dashboard to see the security posture of all their systems at a glance.

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
│ Fastfetch ─┼───┼── POST ───▶│   │Validation│   │
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
| **Fastfetch** | System metadata/identity | All (required!) |

### The "OK" Logic

A system is marked **OK** (green) if it has:
- **Fastfetch** (always required - provides system identity)
- **AND** Lynis (system audit - always needed)
- **AND** Trivy or Vulnix (vulnerability scanner - at least one)

**Rationale:** For ISO compliance, systems need baseline hardening audit (Lynis), identity (Fastfetch), and vulnerability scanning (Trivy or Vulnix depending on OS).

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
  submissions/<SERIAL>/<YYYY-MM-DDTHH-MM-SS>/
      honeybadger-<stamp>.tar.gz
      fastfetch-report.json
      lynis-report.json
      asset-inventory.json
      submission.json
  unmatched/<hostname>-<username>/<timestamp>/
  <YYYY-MM>/                 archive of the pre-serial layout, read-only
```

**Key:** the hardware serial, read from `hardware-serial.txt` in the archive.
`asset_id` is the durable identity; a serial is how a submission finds it, and
one asset may have several over its life.

**No audit period in any path.** It is computed from the submission timestamp.

**Never overwritten.** Two scans of one machine in one round both survive.

**Example:** `webserver01-admin-20260316/`

**Overwrite behavior:** Same-day reports overwrite. Different dates create new directories.

**The record carries the audit's findings.** `submission.json` holds `inventory`
(the findings the client determined, parsed by `parse_asset_inventory()`) and
`inventory_raw` (the document whole, so fields no column shows are not lost).
The findings are denormalised for the same reason `asset_id` and `owner` are: a
closed round has to keep reporting what was true when it was scanned.

`asset-inventory.json` is a summary of the reports, not a report type. It is
recognised by filename in `extract_and_validate_tar()`, carried separately from
`reports`, and never reaches `evaluate_completeness()` - a client that sends
none must not become incomplete for a reason its owner cannot act on. The fleet
view renders it through `INVENTORY_COLUMNS` and `inventory_cell()`, and adds no
colour judgement: the threshold belongs to the ISO process, not the dashboard.

## Authentication

**Added in version 1.1.0** - Mandatory authentication for all endpoints except `/health`.

### Architecture

```
Client (API)                  Server                    Dashboard User
┌──────────────┐             ┌─────────────┐           ┌──────────────┐
│              │             │             │           │              │
│ POST /       ├────Bearer──>│ _validate_  │           │ GET /        │
│              │   Token     │ bearer_     │           │              │
│              │             │ token()     │           │              │
└──────────────┘             └─────────────┘           └──────────────┘
                                    │                          │
                                    ▼                          │
                            VALID_TOKENS list                  │
                            (in memory)                        │
                                                               │
                                                       ┌───────┴──────┐
                                                       │ _validate_   │
                                                       │ basic_auth() │
                                                       └───────┬──────┘
                                                               │
                                                               ▼
                                                       DASHBOARD_PASSWORD
                                                       (in memory)
```

### Design Decisions

**Why two authentication methods?**
- **API clients** (scripts) → Bearer tokens (easy to inject in headers, token per environment)
- **Dashboard users** (humans) → Basic Auth (browser handles UI, single password)

**Why in-memory credential storage?**
- Load once at startup, fail fast if missing/invalid
- No file I/O on hot path (performance)
- Token rotation requires restart (acceptable for internal infrastructure)

**Why no password hashing?**
- Password file protected by OS permissions (chmod 600)
- Server runs as dedicated user
- If attacker has memory access, they already have file access
- Keeps codebase dependency-free

**Why constant-time comparison?**
- `secrets.compare_digest()` prevents timing attacks
- Negligible performance cost
- Security best practice even on internal network

### Implementation Details

**Global Variables (loaded at startup):**
```python
VALID_TOKENS = []           # List of valid Bearer tokens
DASHBOARD_PASSWORD = ""      # Single password for dashboard
```

**Request Flow:**

1. **POST requests** (report submission):
   ```
   do_POST() → _validate_bearer_token() → process request
                      ↓ (if invalid)
                  send 401 JSON error
   ```

2. **GET requests** (dashboard):
   ```
   do_GET() → /health? → yes → return health status (no auth)
                  ↓ no
           _validate_basic_auth() → process request
                  ↓ (if invalid)
              send 401 HTML error with WWW-Authenticate header
   ```

**Error Responses:**
- API endpoints: JSON format `{"error": "message"}`
- Dashboard endpoints: HTML with WWW-Authenticate header (triggers browser login)

**File Formats:**
- `tokens.yaml`: YAML with `tokens:` list
- `password.txt`: Plaintext, first line only, whitespace trimmed

**Security Features:**
- Constant-time token/password comparison
- No credentials in logs
- No fallback/default passwords
- Fail-fast startup validation

### Common Scenarios

**Adding authentication to a new endpoint:**

1. Determine endpoint type:
   - Report submission → Bearer token
   - Dashboard/download → Basic Auth
   - Monitoring → No auth (like `/health`)

2. Add validation at start of handler:
   ```python
   # For API endpoints
   if not self._validate_bearer_token():
       self._send_json_error(401, "Invalid authentication token")
       return

   # For dashboard endpoints
   if not self._validate_basic_auth():
       self._send_html_error(401, "Unauthorized", include_auth_header=True)
       return
   ```

**Rotating tokens:**
1. Edit `tokens.yaml` - add new token
2. Update client scripts with new token
3. Test client can submit reports
4. Remove old token from `tokens.yaml`
5. Restart server
6. Verify old token returns 401

**Changing dashboard password:**
1. Edit `password.txt`
2. Restart server
3. Distribute new password to team
4. Users may need to clear browser auth cache

## Common Tasks

### Adding a new report type

First check it is a report. Something that summarises the reports rather than
being one of them - `asset-inventory.json` is the existing case - is recognised
by filename and carried outside `reports`, so it never enters the requirement
set.

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

### Filtering the round view

The filter lives between `compute_round_state()` and `_round_table()`, and
nowhere else. `generate_round_view_html()` renders every figure - the headline,
the meter, the per-owner bars, the alerts - from the unfiltered state, and only
then calls `filter_round_state()` to build the copy the table is given.

Keep that ordering. It is not a convention, it is the reason `1 of 10 assets
scanned` cannot become a statement about what the reader was looking at: there
is no point in the function where a filter is in scope and a figure has not
been rendered yet. A test asserts the whole progress panel is byte-identical
under every filter in turn.

The pure parts - `parse_round_filters()`, `round_row_matches()`,
`filter_round_state()`, `round_view_href()`, `search_key()` - carry doctests and
know nothing about the handler.

Adding a term means: parse it in `parse_round_filters()`, match it in
`round_row_matches()`, name it in `round_filter_terms()` so the notice can say
it is active, list it in `round_view_href()` so links keep it, offer it in
`_filter_bar()`, and add it to the `carry` list in `generate_round_view_html()`
so changing the round does not drop it.

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
- Filename-based report type detection (lynis.json, fastfetch-report.json, etc.)
- Returns detailed per-file status (HTTP 200/207/400)
- Security: validates paths, enforces size limits (50MB tar, 10MB per file, max 100 files)

**Advantages of tar submission:**
- Reduces network round-trips (4 reports = 1 request vs 4 requests)
- Simplifies client scripts (bundle once, upload once)
- Atomic: all reports for same audit period
- Better for unreliable networks

## Testing

```bash
# Unit and end-to-end tests. Each starts a real server on an ephemeral port
# against a throwaway storage tree and submits a real client archive over HTTP.
python3 -m unittest test_asset_inventory -v

# The pure functions carry doctests
python3 -m doctest honeybadger_server.py -v

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
tar -czf reports.tar.gz test-lynis-report.json test-fastfetch-report.json
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

- **No TLS** - Plain HTTP only
- **No rate limiting** - Can be flooded
- **No retention policy** - Reports accumulate forever
- **No database** - Filesystem only (slow with thousands of reports)
- **No pagination** - Dashboard loads all reports at once
- **Single threaded** - Python http.server limitation

These are **by design** for simplicity. If you need these, consider if the project is growing beyond its intended use case.

## When to Refactor

The single-file principle has expired. It was worth keeping while the server
was a drop box; it stopped being worth keeping once the server acquired
authentication, an asset register, two dashboard views and a storage model with
its own lifecycle rules. The file is around 3000 lines and three of the five
original triggers below have already fired.

The original triggers, for the record:
- Adding >2 new report types
- Adding authentication system          (done - version 1.1.0)
- Adding database backend               (queued - bean badgersbay-8ylz)
- Adding API versioning
- Team size > 2 developers

Split along the seams the code already has rather than by line count:

| Module | Contains |
|--------------|-------------------------------------------------------|
| register | AssetRegister, serial normalisation, owner slugs |
| periods | audit period, round windows, on-time classification |
| storage | submission records, evidence serving |
| index | ComplianceCache, round state computation |
| views | round view, fleet view, legacy dashboard |
| server | config, auth, routing |

Do it when the next change would otherwise add a sixth concern to the file, not
as a project of its own.

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
- Code: Read `honeybadger_server.py` - around 3000 lines

## Git Commit Guidelines

**IMPORTANT:** Never mention AI assistance in commit messages:
- **DO NOT** add "Co-Authored-By: Claude" or similar attributions
- **DO NOT** mention "AI-generated", "AI-assisted", or "Claude" anywhere in commit messages
- Commit messages should reflect the technical changes only
- Keep commits professional and focused on the work itself
