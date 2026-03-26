# Report Storage

## Overview

Reports are stored on the filesystem in a date-organized directory structure. Each unique combination of hostname, username, and date gets its own directory.

## Storage Structure

### Requirement: Directory structure based on audit periods

The system SHALL store reports in directories organized by audit period instead of individual upload dates when compliance mode is enabled.

**Directory Format (compliance enabled):** `{YYYY-MM}/{hostname}-{username}/`

Where:
- `YYYY-MM`: Audit period (year and audit month)
- `hostname`: From X-Hostname header
- `username`: From X-Username header

**Directory Format (legacy mode):** `{hostname}-{username}-{YYYYMMDD}/`

#### Scenario: Compliance mode storage structure
- **WHEN** compliance.enabled is true
- **THEN** reports stored in `./reports/2026-03/webserver01-admin/`

#### Scenario: Legacy mode storage structure
- **WHEN** compliance.enabled is false or not configured
- **THEN** reports stored in `./reports/webserver01-admin-20260316/`

#### Scenario: System directory within audit period
- **WHEN** webserver01 (user admin) uploads to audit period 2026-03
- **THEN** reports stored in `./reports/2026-03/webserver01-admin/lynis-report.json`

#### Scenario: Upload date mapping
- **WHEN** upload received on 2026-04-15 with audit_months [3, 9]
- **THEN** stored in `./reports/2026-09/` (next audit period)

#### Scenario: User changes for same hostname
- **WHEN** webserver01 uploads with user "admin" then later with user "sysadmin"
- **THEN** creates separate directories: `webserver01-admin/` and `webserver01-sysadmin/`

### Example (Legacy Mode)

```
<storage_location>/
  └── <hostname>-<username>-<yyyymmdd>/
      ├── lynis-report.json
      └── neofetch-report.json
```

```
./reports/
  ├── webserver01-admin-20260316/
  │   ├── lynis-report.json
  │   └── neofetch-report.json
  └── nixos-prod-sysadmin-20260315/
      ├── lynis-report.json
      └── neofetch-report.json
```

### Example (Compliance Mode)

```
./reports/
  ├── 2026-03/
  │   ├── webserver01-admin/
  │   │   ├── lynis-report.json
  │   │   └── neofetch-report.json
  │   └── nixos-prod-sysadmin/
  │       ├── lynis-report.json
  │       └── neofetch-report.json
  └── 2026-09/
      └── webserver01-admin/
          ├── lynis-report.json
          └── neofetch-report.json
```

## Directory Naming

**Legacy Format:** `<hostname>-<username>-<yyyymmdd>`

- `hostname`: From `X-Hostname` header or JSON field
- `username`: From `X-Username` header or JSON field
- `yyyymmdd`: Current date when report is received (YYYYMMDD format)

**Compliance Format:** `<YYYY-MM>/<hostname>-<username>`

- `YYYY-MM`: Calculated audit period
- `hostname`: From `X-Hostname` header or JSON field
- `username`: From `X-Username` header or JSON field

## Requirement: File Naming

Each report type SHALL map to a specific filename in the host directory.

| Report Type | Filename |
|-------------|----------|
| lynis | `lynis-report.json` |
| neofetch | `neofetch-report.json` |

#### Scenario: Lynis report storage
- **WHEN** server receives a valid lynis report
- **THEN** server stores it as `lynis-report.json` in the appropriate host directory

#### Scenario: Neofetch report storage
- **WHEN** server receives a valid neofetch report
- **THEN** server stores it as `neofetch-report.json` in the appropriate host directory

## Overwrite Behavior

### Requirement: Overwrite behavior in audit periods

The system SHALL overwrite reports when same hostname-username combination uploads multiple times to the same audit period.

#### Scenario: Multiple uploads same audit period
- **WHEN** webserver01-admin uploads on 2026-02-10 and 2026-03-15 (both map to 2026-03)
- **THEN** second upload overwrites first in `./reports/2026-03/webserver01-admin/`

#### Scenario: Different audit periods preserved
- **WHEN** webserver01-admin uploads to 2026-03 period and later to 2026-09 period
- **THEN** both audit period directories contain separate reports for same hostname-username

#### Scenario: Same hostname different users
- **WHEN** webserver01 uploads as "admin" and "sysadmin" in same period
- **THEN** separate directories: `webserver01-admin/` and `webserver01-sysadmin/`

### Legacy Mode Behavior

**Same date:** Reports received on the same day overwrite previous reports for that host-user combination.

**Different date:** New directory created, previous days' reports remain.

**Rationale:** Allows re-running scans throughout the day without creating duplicates.

## Configuration

Controlled via `config.yaml`:

```yaml
storage_location: ./reports
```

**Default:** `./reports` (relative to server working directory)

## Storage Operations

### Directory Creation

- Parent directories created automatically (`parents=True`)
- No error if directory exists (`exist_ok=True`)
- Permissions: Inherits from parent directory

### File Writing

- JSON formatted with 2-space indentation
- File encoding: UTF-8
- Overwrites existing files without warning

### Security

**Path Traversal Protection:**

When serving reports via HTTP, paths are validated:

```python
# Resolve to absolute path
full_path = full_path.resolve()
storage_path = Path(storage_location).resolve()

# Reject if outside storage directory
if not str(full_path).startswith(str(storage_path)):
    return 403 Forbidden
```

## Implementation Location

- Save logic: `honeybadger_server.py:save_report()` (line 224)
- Security check: `honeybadger_server.py:do_GET()` (line 759-765)
- Directory creation: `run_server()` (line 802)

## Disk Usage Considerations

- **No cleanup mechanism** - reports accumulate indefinitely
- **No compression** - JSON stored uncompressed
- **No archival** - old reports remain on disk
- Each report typically: 1-50 KB (Lynis), 10-500 KB (Trivy)

## Future Considerations

- Retention policy / automatic cleanup
- Compression for old reports
- External storage backends (S3, etc.)
- Database indexing for faster queries
- Report deduplication across dates
