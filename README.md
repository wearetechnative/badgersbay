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

A line whose first non-whitespace character is `#` is a note and is skipped.
Notes may sit above the header and between rows, and nothing is parsed out of
them - they are prose for whoever edits the file next:

```csv
# TARI-00031 carries the serial the machine reports. The ISO tool holds
# AC06CMEP, the suffix of its hostname - do not "correct" this row to it.
TARI-00031,YD063JGA,Elma Aker,ThinkPad,windows,active,2023-06-12,2023-06-12,,
```

The register contains names paired with hardware serials. Keep it out of the
repository - `assets.csv` is gitignored, and in production it is delivered as
an agenix secret. It is therefore never seen in a diff or a review, which is
what the notes are for.

### Validation

The server refuses to start on a register it cannot trust: a duplicate active
serial, an unknown class or status, an unparseable date, or two rows claiming
one serial for overlapping periods. A compliance figure built on an ambiguous
register is worse than no figure. An absent register is not an error - the
server still accepts submissions, it just cannot report who is missing.

## Accounting for an Asset That Cannot Be Scanned

An asset that cannot be scanned in a round is a deviation, justified in the ISO
tool. This server does not hold that justification - it records that one exists,
so the round can close instead of showing a permanently red row nobody can act
on.

On the round view, each outstanding row carries a control: a required reason,
your name, and a button. The asset moves to **accounted for**, which is counted
separately from **scanned**:

```
8 scanned · 2 accounted for · 1 outstanding
```

Not `10 / 11 OK`. Folding the two together would merge "we hold evidence" with
"we hold an excuse", and the deviation count is what the ISO tool needs as its
own figure. The round is closeable when nothing is outstanding.

Exceptions are keyed on asset and round, stored under
`reports/exceptions/<period>/<asset_id>.json`. An asset unreachable in September
may be perfectly reachable in March, so nothing carries over when the next round
opens and nothing needs clearing.

**A submission always wins.** If an accounted-for asset submits after all, the
submission counts and the exception lapses without anyone withdrawing it.

The dashboard uses a single shared password, so the name recorded is what the
operator typed. It is shown as self-reported and must not be read as an
authenticated identity.

## Storage Layout

A submission is the unit: one upload, one moment, stored under the hardware
serial that identifies the asset.

```
reports/
  submissions/PF50L2MR/2026-09-15T13-25-34/
      honeybadger-20260915-132534.tar.gz   the archive, kept whole
      fastfetch-report.json                extracted
      lynis-report.json                    extracted
      asset-inventory.json                 extracted, the client's findings
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

Both are settled by reading what the machine actually sent, so the round view
links each unmatched submission's reports and archive beside its reason. The
evidence route names the tree it serves from -
`/evidence/unmatched/<hostname>-<username>/<timestamp>/<file>` beside
`/evidence/submissions/<serial>/<timestamp>/<file>` - and serves only the two
trees the server writes. The `2026-03/` archive is history it reads and never
writes, and is not reachable through it.

## The Audit's Findings

The client determines the values the ISO register needs and ships them in
`asset-inventory.json`. The server reads them so they can be read off the
dashboard rather than retyped into the spreadsheet by hand.

`submission.json` carries them twice, on purpose:

| Field | Holds |
|-----------------|--------------------------------------------------------|
| `inventory` | the findings, denormalised beside `asset_id` and `owner` |
| `inventory_raw` | the document whole, including fields no column shows |

The findings are denormalised for the same reason the owner is: the register
moves, the client moves, and a closed round has to keep reporting what was true
when it was scanned. The document is kept whole because the client runs ahead
of the server and always will - storing only what is modelled today would throw
the rest away at the door.

The **All assets** view has a column for each of disk encryption, screen lock,
firewall, hardening score and OS currency. Each cell shows the value the client
determined; hovering it shows the finding that value came from, so an auditor
asking "how do you know" can be answered without unpacking the archive. The
inventory is also stored beside the reports, so it downloads like any other
piece of evidence.

**Unknown is not a failure.** A cell reads `unknown` in three situations, and
none of them is the asset's fault:

- the client sent no inventory (an older client, or a Windows asset);
- this generation of the client does not report that field;
- the client deliberately declined to assert a value, in which case its reason
  is shown rather than left blank.

**No value is coloured as a pass or a failure.** Whether a hardening score of
62 is acceptable is a threshold the ISO process owns. The client already
reports its own verdict in the finding text; the dashboard shows the number and
that text and adds no judgement of its own.

The inventory is a summary of the reports, not a report. It never counts toward
completeness, so a client that sends none is not incomplete for a reason its
owner cannot act on. A document declaring a `schema_version` the server does
not recognise is stored whole and rendered for the fields it does understand;
one that cannot be parsed at all is logged, reported back to the client, and
skipped, and the submission is stored regardless.

Submissions already on disk are not re-read. Their columns stay empty until the
asset submits again.

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

## Narrowing the Round View

The round view's table can be narrowed without changing what the round says.

| Term    | Matches                                                                   |
|---------|---------------------------------------------------------------------------|
| `state` | `scanned`, `accounted`, `outstanding`, `unexplained`, `manual`, `retired` |
| `owner` | The owner as the register holds it, ignoring case                         |
| `class` | `linux`, `macos` or `windows`                                             |
| `q`     | Part of an asset id or a hardware serial                                  |

```
/?view=round&period=2026-09&state=outstanding&owner=Pim+Snel
```

The terms are query parameters, so a filtered view survives a reload and can be
pasted into a message to the person who owes a scan - which is the main thing
anyone does with a filter here. They compose with the round selector, which
carries them when the round changes.

`q` folds case and separators away on both sides, so a serial written with the
hyphen the ISO tool uses and the same serial as the machine reports it find the
same asset. `TARI-00031`, `00031` and `31` all reach TARI-00031.

**The figures never move.** `1 of 10 assets scanned`, the meter, the per-owner
bars and the bucket counts are statements about the round, and they are computed
before the filter is applied. A compliance number that changed with what the
reader was looking at would eventually be screenshotted into an audit file.

The view says which filter is active and how many assets it hides, with a link
back to the whole round. It says so even when the filter hides nothing, because
a shared address with an inert filter would otherwise read as the full picture.
An empty table under a filter and an empty round look identical and mean
opposite things, so they do not read the same.

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

`asset-inventory.json` is not in this table. It summarises what the reports
say rather than being one of them, so it never counts toward completeness. See
[The Audit's Findings](#the-audits-findings).

## Testing

```bash
# End-to-end tests. Each starts a real server on an ephemeral port against a
# throwaway storage tree and submits a real client archive over HTTP.
python3 -m unittest test_asset_inventory -v

# The pure functions carry doctests
python3 -m doctest honeybadger_server.py -v
```

`test-archive-current-client.tar.gz` was produced by the honeybadger client,
not written by hand.

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
