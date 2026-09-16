# Honeybadger Server

Centralized security report aggregation server for collecting vulnerability scan results from multiple hosts.

## Quick Start

### Prerequisites

- Python 3.7+
- PyYAML

```bash
pip install -r requirements.txt
```

### Authentication Setup (Required)

**BREAKING CHANGE**: As of version 1.1.0, authentication is mandatory. The server will not start without auth files.

Create two authentication files:

**1. Token file (YAML format)**
```bash
cat > tokens.yaml <<EOF
tokens:
  - hb_token_$(openssl rand -hex 16)
  - hb_token_$(openssl rand -hex 16)
EOF
```

**2. Password file (plaintext)**
```bash
openssl rand -base64 24 > password.txt
```

### Start Server

```bash
./honeybadger_server.py \
  --token-file tokens.yaml \
  --dashboard-password-file password.txt
```

The server will:
1. Load authentication credentials
2. Load configuration from `config.yaml` (or use `--config` to specify location)
3. Start listening on the configured port (default: 7123)

## Authentication

The server uses two separate authentication mechanisms:

### API Authentication (Bearer Tokens)

All report submission endpoints require a valid Bearer token in the `Authorization` header.

**Token File Format** (`tokens.yaml`):
```yaml
tokens:
  - hb_production_token_abc123
  - hb_staging_token_xyz789
```

- Multiple tokens supported (for different clients/environments)
- Whitespace is automatically trimmed
- Tokens are validated using constant-time comparison (timing-attack resistant)

### Dashboard Authentication (HTTP Basic Auth)

Web dashboard access requires HTTP Basic Authentication.

**Password File Format** (`password.txt`):
```
my_secure_password_123
```

- Single password for all dashboard users
- Only first line is used (extra lines logged as warning)
- Whitespace is automatically trimmed
- Username is ignored - any username works with the correct password

## Submitting Reports

### Single Report Submission

Submit individual reports with Bearer token authentication:

```bash
# Fastfetch (system info)
curl -X POST http://server:7123/ \
  -H "Authorization: Bearer hb_production_token_abc123" \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-Report-Type: fastfetch" \
  -d @fastfetch-report.json

# Lynis (hardening audit)
curl -X POST http://server:7123/ \
  -H "Authorization: Bearer hb_production_token_abc123" \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-Report-Type: lynis" \
  -d @lynis-report.json

# Trivy (vulnerability scanner)
curl -X POST http://server:7123/ \
  -H "Authorization: Bearer hb_production_token_abc123" \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-Report-Type: trivy" \
  -d @trivy-report.json

# Vulnix (NixOS vulnerability scanner)
curl -X POST http://server:7123/ \
  -H "Authorization: Bearer hb_production_token_abc123" \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-Report-Type: vulnix" \
  -d @vulnix-report.json
```

### Tar Archive Submission

Submit multiple reports in a single request:

```bash
# Create archive with all reports
tar -czf reports.tar.gz \
  fastfetch-report.json \
  lynis-report.json \
  trivy-report.json

# Submit archive
curl -X POST http://server:7123/submit-tar \
  -H "Authorization: Bearer hb_production_token_abc123" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  --data-binary @reports.tar.gz
```

### Authentication Errors

**Missing token:**
```json
{"error": "Missing Authorization header"}
```

**Invalid token:**
```json
{"error": "Invalid authentication token"}
```

**Malformed header:**
```json
{"error": "Invalid Authorization header format. Expected: Bearer <token>"}
```

## Asset Register

The register is the denominator compliance is measured against. Without it the
dashboard can show what arrived but never which systems are missing - and an
asset that never reports is exactly what an audit needs to surface.

Export the `Active Assets` sheet from the ISO compliance workbook to CSV and
point `compliance.asset_register` at it. See `assets.csv.example`.

```csv
asset_id,serial,owner,model,class,status,owner_since,valid_from,valid_to,departure_reason
TARI-00023,PF50L2MR,Wouter van der Toorren,LENOVO 21K9CTO1WW,linux,active,2024-01-01,2024-01-01,,
```

| Column | Meaning |
|--------------------|-----------------------------------------------------------|
| `asset_id` | Durable identity, as held in the ISO register |
| `serial` | Hardware serial; the key an incoming submission matches on |
| `owner` | Person responsible; drives the call list and file naming |
| `class` | `linux`, `macos` or `windows`; decides what a complete set is |
| `status` | `active` or `retired`; retired is excluded from the count |
| `owner_since` | Evidence older than this predates the current holder |
| `valid_from` | When this serial entered scope |
| `valid_to` | When it left; blank means still in scope |
| `departure_reason` | Why it left. A departure without one is reported, not subtracted |

An asset may hold several serials over its life. Give each its own row with its
own validity window, and the history stays continuous across a replacement:

```csv
TARI-00037,PF3NFHJL,Pankhuri Prakash,Ideapad 3,linux,active,2024-01-01,2024-01-01,2026-08-01,replaced
TARI-00037,MP1Y69AC,Pankhuri Prakash,IdeaPad 5,linux,active,2026-08-01,2026-08-01,,
```

The register contains names paired with hardware serials. Keep it out of the
repository - `assets.csv` is gitignored, and in production it is delivered as
an agenix secret.

### Validation

The server refuses to start on a register it cannot trust: a duplicate active
serial, an unknown class or status, an unparseable date, or two rows claiming
one serial for overlapping periods. A compliance figure built on an ambiguous
register is worse than no figure. An absent register is not an error - the
server still accepts submissions, it just cannot report who is missing.

## Storage Layout

A submission is the unit: one upload, one moment, stored under the hardware
serial that identifies the asset.

```
reports/
  submissions/PF50L2MR/2026-09-15T13-25-34/
      honeybadger-20260915-132534.tar.gz   the archive, kept whole
      fastfetch-report.json                extracted
      lynis-report.json                    extracted
      submission.json                      what this submission was
  unmatched/<hostname>-<username>/<timestamp>/
  2026-03/                                 archive of the pre-serial layout
```

Records are never overwritten, so two scans of one machine in the same round
both survive. No audit period appears in any path: the period is computed from
the timestamp, so changing `audit_months` reclassifies history instead of
leaving directory names that quietly mean something else.

A submission that cannot be attributed is stored, never rejected. The two ways
that happens need different fixes and are reported separately: `no_serial` is a
client problem, `serial_not_in_register` is a register problem.

## Audit Rounds

A round opens in its audit month and stays open until the next begins. A
submission belongs to the most recent audit month at or before its date -
scanning a fleet takes weeks, and a round that ran into the following month
keeps its late submissions rather than filing them into one that has not
started.

Each round has two windows. The **scan window** is the audit month plus
`grace_weeks`: it decides which assets belong to the round and whether a
submission is on time. The **coverage window** runs until the next round opens
and is the period the round makes a statement about.

Assets fall into five states, kept apart on purpose:

| State | Meaning |
|---------------|--------------------------------------------------------|
| scanned | A submission exists for this round |
| accounted for | Left scope during the round, with a reason recorded |
| outstanding | In scope, nothing received |
| unexplained | Left scope with no reason given |
| manual | Client cannot submit yet (Windows) |

Accounted-for is not scanned. Folding the two together would merge "we hold
evidence" with "we hold an excuse", and the deviation count is what the ISO
tool needs as its own figure.

## Dashboard Access

### Browser Access

1. Open `http://server:7123/` in your browser
2. Browser will show a login dialog
3. Enter any username and the password from `password.txt`
4. Dashboard displays compliance status for all systems

**Browser Behavior:**
- Login prompt appears automatically on first visit
- Browser caches credentials for the session
- To log out: close browser or use browser's "forget password" feature

### Command Line Access

```bash
# View dashboard HTML
curl -u admin:your_password http://server:7123/

# Download report
curl -u admin:your_password \
  http://server:7123/reports/2026-03/hostname-user/lynis-report.json \
  -o lynis-report.json
```

## Health Check Endpoint

The `/health` endpoint is **unauthenticated** for monitoring systems:

```bash
curl http://server:7123/health
```

Returns:
```json
{
  "status": "ok",
  "http_code": 200,
  "service": "honeybadger-server",
  "uptime": {"seconds": 3600, "human_readable": "1h 0m"},
  "statistics": {
    "total_report_directories": 42,
    "unique_hosts": 10,
    "reports_by_type": {"lynis": 40, "fastfetch": 42}
  }
}
```

## CLI Arguments

```
usage: honeybadger_server [-h] [--config PATH] --token-file PATH
                          --dashboard-password-file PATH [--version]

Required Arguments:
  --token-file PATH              Path to YAML file containing API tokens
  --dashboard-password-file PATH Path to plaintext file with dashboard password

Optional Arguments:
  --config PATH                  Path to configuration file
                                (default: search working dir, script dir, /etc/honeybadger/)
  --version                     Show version and exit
  -h, --help                    Show this help message
```

## Deployment

### Systemd Service Example

```ini
[Unit]
Description=Honeybadger Security Report Server
After=network.target

[Service]
Type=simple
User=honeybadger
WorkingDirectory=/opt/honeybadger
ExecStart=/opt/honeybadger/honeybadger_server.py \
  --config /etc/honeybadger/config.yaml \
  --token-file /run/agenix/honeybadger-tokens.yaml \
  --dashboard-password-file /run/agenix/honeybadger-password.txt
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

### NixOS with agenix

```nix
{ config, pkgs, ... }:
{
  age.secrets = {
    honeybadger-tokens = {
      file = ./secrets/honeybadger-tokens.yaml.age;
      owner = "honeybadger";
    };
    honeybadger-password = {
      file = ./secrets/honeybadger-password.txt.age;
      owner = "honeybadger";
    };
  };

  systemd.services.honeybadger = {
    description = "Honeybadger Security Report Server";
    after = [ "network.target" ];
    wantedBy = [ "multi-user.target" ];

    serviceConfig = {
      Type = "simple";
      User = "honeybadger";
      WorkingDirectory = "/var/lib/honeybadger";
      ExecStart = ''
        ${pkgs.python3}/bin/python3 /opt/honeybadger/honeybadger_server.py \
          --config /etc/honeybadger/config.yaml \
          --token-file ${config.age.secrets.honeybadger-tokens.path} \
          --dashboard-password-file ${config.age.secrets.honeybadger-password.path}
      '';
      Restart = "on-failure";
    };
  };
}
```

## Breaking Changes

### Version 1.1.0: Mandatory Authentication

**What changed:**
- `--token-file` and `--dashboard-password-file` CLI arguments are now **required**
- Server will not start without authentication files
- All POST endpoints require Bearer token authentication
- All GET endpoints (except `/health`) require Basic Auth

**Migration steps:**

1. **Generate authentication files** (before upgrading):
   ```bash
   # Create token file
   cat > /etc/honeybadger/tokens.yaml <<EOF
   tokens:
     - hb_$(openssl rand -hex 16)
   EOF

   # Create password file
   openssl rand -base64 24 > /etc/honeybadger/password.txt
   chmod 600 /etc/honeybadger/tokens.yaml /etc/honeybadger/password.txt
   chown honeybadger:honeybadger /etc/honeybadger/*.{yaml,txt}
   ```

2. **Update systemd unit** or deployment scripts to include auth arguments

3. **Update client scripts** to include `Authorization: Bearer <token>` header

4. **Distribute tokens** to all client systems

5. **Share dashboard password** with team via password manager

6. **Upgrade server** - it will now enforce authentication

7. **Test authentication**:
   ```bash
   # Test API (should return 401 without token)
   curl -X POST http://server:7123/

   # Test API with token (should work)
   curl -X POST http://server:7123/ \
     -H "Authorization: Bearer your_token" \
     -H "X-Hostname: test" \
     -H "X-Username: test" \
     -H "X-Report-Type: fastfetch" \
     -d '{"os": "NixOS"}'

   # Test dashboard (should prompt for password)
   curl http://server:7123/

   # Test health check (should work without auth)
   curl http://server:7123/health
   ```

**Rollback:**
If you need to rollback, downgrade to version 1.0.x and remove auth arguments from systemd unit.

## Report Types

| Type | Purpose | Required |
|------|---------|----------|
| **Fastfetch** | System metadata (hostname, OS, kernel) | Always |
| **Lynis** | System hardening audit | Always |
| **Trivy** | Container/OS vulnerability scanner | One of Trivy or Vulnix |
| **Vulnix** | NixOS vulnerability scanner | One of Trivy or Vulnix |

A system is marked "Complete" when it has:
- Fastfetch (identity)
- Lynis (hardening audit)
- Trivy OR Vulnix (vulnerability scan)

## Configuration File

See `config.yaml` for storage location, network port, and compliance settings.

## Security Considerations

- **Token storage**: Tokens are loaded into memory at startup and never written to logs
- **Password storage**: Password stored in plaintext file (protect with OS file permissions)
- **Timing attacks**: Token/password comparisons use `secrets.compare_digest()`
- **Token rotation**: Restart server after updating `tokens.yaml`
- **No rate limiting**: Deploy behind firewall or reverse proxy with rate limiting
- **File permissions**: Ensure auth files are readable only by server user (chmod 600)

## Troubleshooting

### Server won't start

**Error: "Token file not found"**
- Check path in `--token-file` argument
- Verify file exists and is readable by server user

**Error: "Token file missing 'tokens' key"**
- Ensure YAML file has `tokens:` key with list of tokens
- Check YAML syntax with `python3 -c "import yaml; yaml.safe_load(open('tokens.yaml'))"`

**Error: "Dashboard password file is empty"**
- Ensure password.txt contains at least one non-whitespace character

### Authentication failures

**API returns 401**
- Verify token in `Authorization: Bearer <token>` header
- Check token exists in tokens.yaml (case-sensitive, no extra whitespace)
- Check server logs for "Loaded N token(s)" message at startup

**Dashboard prompts for password repeatedly**
- Verify password matches first line of password.txt (case-sensitive)
- Check browser isn't blocking cookies
- Try different username (username is ignored, but required by Basic Auth)

**Health check returns 401**
- Health check should work without auth - this indicates a bug
- Check you're requesting `/health` not `/` or `/status`

## License

See LICENSE file.
