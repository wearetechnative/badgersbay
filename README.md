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
# Neofetch (system info)
curl -X POST http://server:7123/ \
  -H "Authorization: Bearer hb_production_token_abc123" \
  -H "Content-Type: application/json" \
  -H "X-Hostname: $(hostname)" \
  -H "X-Username: $(whoami)" \
  -H "X-Report-Type: neofetch" \
  -d @neofetch-report.json

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
  neofetch-report.json \
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
    "reports_by_type": {"lynis": 40, "neofetch": 42}
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
     -H "X-Report-Type: neofetch" \
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
| **Neofetch** | System metadata (hostname, OS, kernel) | Always |
| **Lynis** | System hardening audit | Always |
| **Trivy** | Container/OS vulnerability scanner | One of Trivy or Vulnix |
| **Vulnix** | NixOS vulnerability scanner | One of Trivy or Vulnix |

A system is marked "Complete" when it has:
- Neofetch (identity)
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
