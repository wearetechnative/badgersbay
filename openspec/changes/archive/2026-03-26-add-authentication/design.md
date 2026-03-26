# Authentication Design

## Context

The Honeybadger server is currently unauthenticated and deployed on internet-facing infrastructure. This creates two security risks:

1. **API abuse**: Anyone can POST fake reports, polluting the compliance database
2. **Data exposure**: Sensitive audit data (vulnerabilities, system configurations) is publicly accessible

The server follows a single-file architecture using Python's `http.server` module with a custom `RequestHandler`. All logic resides in `honeybadger_server.py` (~800 lines). The design must maintain this simplicity while adding mandatory authentication.

**Current request flow:**
```
HTTP Request → do_GET() or do_POST() → validate → process → respond
```

**Deployment context:**
- NixOS infrastructure with agenix for secret management
- Secrets injected as file paths via systemd service configuration
- No access to secret management UI from Honeybadger server code
- Multiple client systems submitting reports via cron jobs

## Goals / Non-Goals

**Goals:**
- Block unauthorized API submissions (POST endpoints)
- Block unauthorized dashboard access (GET endpoints except /health)
- Fail fast at startup if authentication not configured
- Maintain single-file architecture with no new external dependencies
- Support standard HTTP authentication (Bearer tokens, Basic Auth)
- Enable NixOS/agenix deployment pattern (externally managed secrets)

**Non-Goals:**
- Token generation or rotation (handled by deployment system)
- Password hashing (deployment manages secrets, plaintext sufficient for file storage)
- User management UI (static configuration only)
- Rate limiting or brute force protection (rely on infrastructure firewalls)
- Session management (stateless - credentials sent per request)
- OAuth/OIDC/SAML (overkill for internal infrastructure)

## Decisions

### 1. Two Authentication Mechanisms

**Decision:** Use Bearer tokens for API endpoints and HTTP Basic Auth for dashboard.

**Rationale:**
- **API clients** (automated scripts) benefit from Bearer tokens - easy to inject in headers
- **Dashboard users** (humans in browsers) benefit from Basic Auth - browser handles login UI
- Separation prevents accidental credential leakage (API token != dashboard password)
- Standard patterns (RFC 6750, RFC 7617) enable curl/browser interoperability

**Alternatives considered:**
- **Single password for everything**: Rejected - reusing credentials across API and UI violates principle of least privilege
- **Only tokens**: Rejected - requires client-side token management UI or browser extensions
- **Only Basic Auth**: Rejected - automating header generation from password is awkward for scripts

### 2. In-Memory Credential Storage

**Decision:** Load credentials once at startup, keep in memory, never reload during runtime.

**Rationale:**
- Matches server's stateless design (no dynamic configuration)
- Avoids file I/O on every request (performance)
- Fail-fast startup validation catches misconfigurations immediately
- Secret rotation requires service restart (acceptable for internal infrastructure)

**Alternatives considered:**
- **Reload on every request**: Rejected - adds file I/O to hot path, complicates error handling
- **Periodic reload**: Rejected - adds complexity (threading, signals) and startup failure is sufficient

**Implementation:**
```python
# Global variables loaded at startup
VALID_TOKENS = []  # List of valid Bearer tokens
DASHBOARD_PASSWORD = ""  # Single password for dashboard

def load_credentials(token_file, password_file):
    global VALID_TOKENS, DASHBOARD_PASSWORD
    # Load once, fail if missing/invalid
```

### 3. Middleware Pattern for Authentication

**Decision:** Add authentication checks at the start of `do_GET()` and `do_POST()` methods.

**Rationale:**
- Minimal code change (single-file architecture)
- Early return on auth failure prevents processing invalid requests
- Explicit auth checks per method (GET vs POST) enable different auth strategies
- No need for decorator pattern or separate middleware class

**Implementation:**
```python
def do_POST(self):
    # Check Bearer token first
    if not self._validate_bearer_token():
        self._send_json_error(401, "Invalid authentication token")
        return

    # Continue with existing POST logic
    if self.path == '/submit-tar':
        # ... existing code
```

**Alternatives considered:**
- **Decorator pattern**: Rejected - adds complexity for minimal benefit in single-file
- **Separate middleware class**: Rejected - breaks single-file architecture

### 4. Token File Format: YAML

**Decision:** Use YAML format with `tokens:` list for API tokens.

**Rationale:**
- PyYAML already in dependencies (for config.yaml)
- List format makes it obvious that multiple tokens are supported
- Easy for humans to read/edit compared to JSON
- Matches existing config.yaml pattern

**Format:**
```yaml
tokens:
  - hb_prod_token_abc123
  - hb_staging_token_xyz789
```

**Alternatives considered:**
- **JSON**: Rejected - less human-friendly, requires quotes
- **Plain text (one per line)**: Rejected - ambiguous format (what about empty lines? comments?)
- **Environment variable**: Rejected - doesn't support multiple tokens cleanly

### 5. Password File Format: Plaintext

**Decision:** Store dashboard password as plaintext in a file, trim whitespace, use first line only.

**Rationale:**
- agenix/NixOS manages encryption at rest (file permissions, encrypted storage)
- No bcrypt needed - file only readable by honeybadger user
- Simpler than YAML (no key name needed, just the secret)
- Matches common secret file patterns (e.g., database passwords)

**Format:**
```
my_secure_password_123
```

**Alternatives considered:**
- **YAML with key**: Rejected - unnecessary structure for single value
- **Hashed (bcrypt/argon2)**: Rejected - adds dependency, provides no benefit when file is already protected by OS permissions
- **Base64 encoded**: Rejected - security theater, doesn't prevent reading by server user

### 6. CLI Arguments: Required, No Fallback

**Decision:** Use argparse with `required=True` for both `--token-file` and `--dashboard-password-file`. No default paths.

**Rationale:**
- Fail-fast: Server won't start without explicit auth configuration
- Matches config file pattern (already requires `--config` in systemd units)
- Explicit is better than implicit (Zen of Python)
- Prevents accidental unauthenticated deployment

**Implementation:**
```python
parser.add_argument('--token-file', required=True,
                   help='Path to YAML file containing valid API tokens')
parser.add_argument('--dashboard-password-file', required=True,
                   help='Path to plaintext file containing dashboard password')
```

**Alternatives considered:**
- **Default to ~/.honeybadger/tokens.yaml**: Rejected - makes unauthenticated start possible if forgotten
- **Environment variables**: Rejected - file paths are clearer in systemd unit files
- **Optional arguments**: Rejected - defeats the purpose of mandatory auth

### 7. Constant-Time Token Comparison

**Decision:** Use `secrets.compare_digest()` for Bearer token validation.

**Rationale:**
- Prevents timing attacks (though unlikely on internal network, good practice)
- Standard library function (no new dependency)
- Negligible performance cost

**Implementation:**
```python
import secrets

def _validate_bearer_token(self):
    auth_header = self.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return False
    token = auth_header[7:]  # Remove "Bearer " prefix
    return any(secrets.compare_digest(token, valid) for valid in VALID_TOKENS)
```

**Alternatives considered:**
- **Simple `==` comparison**: Rejected - timing attacks are a known vulnerability
- **Hash comparison**: Rejected - tokens are already secrets, hashing doesn't help

### 8. Basic Auth Header Parsing

**Decision:** Use base64 decoding to extract password from Basic Auth header, ignore username.

**Rationale:**
- RFC 7617 standard format: `Authorization: Basic base64(username:password)`
- Username is ignored (single-user system - only password matters)
- Python stdlib `base64` module sufficient

**Implementation:**
```python
import base64

def _validate_basic_auth(self):
    auth_header = self.headers.get('Authorization', '')
    if not auth_header.startswith('Basic '):
        return False

    try:
        encoded = auth_header[6:]  # Remove "Basic " prefix
        decoded = base64.b64decode(encoded).decode('utf-8')
        _, password = decoded.split(':', 1)  # Ignore username
        return secrets.compare_digest(password, DASHBOARD_PASSWORD)
    except Exception:
        return False  # Malformed header
```

**Alternatives considered:**
- **Require specific username**: Rejected - adds complexity for no security benefit
- **Plain password header**: Rejected - non-standard, breaks browser integration

### 9. Error Response Format

**Decision:** Return JSON for API endpoints (401), plain text + WWW-Authenticate for dashboard (401).

**Rationale:**
- **API clients** expect JSON errors (matches existing report submission responses)
- **Browsers** expect WWW-Authenticate header to trigger login dialog
- Different audiences, different formats

**Implementation:**
```python
# API endpoint (POST)
{"error": "Invalid authentication token"}

# Dashboard endpoint (GET)
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Basic realm="Honeybadger Dashboard"
Content-Type: text/html
<html><body>Authentication required</body></html>
```

**Alternatives considered:**
- **Same format for both**: Rejected - breaks browser login dialog behavior
- **HTML for API errors**: Rejected - scripts expect JSON

### 10. Health Endpoint Exception

**Decision:** `/health` endpoint remains unauthenticated.

**Rationale:**
- Monitoring systems (Prometheus, Nagios) need to check liveness without credentials
- Health check doesn't expose sensitive data (just uptime and report counts)
- Standard practice for containerized services

**Implementation:**
```python
def do_GET(self):
    if self.path == '/health':
        # Skip auth check
        self.handle_health()
        return

    # All other GET paths require auth
    if not self._validate_basic_auth():
        # ...
```

## Risks / Trade-offs

### Risk: Token Leakage in Logs

**Risk:** Bearer tokens could be logged if clients send them incorrectly (e.g., in query params instead of headers).

**Mitigation:**
- Never log Authorization headers
- Existing log statements only log paths and status codes (already safe)
- Document correct usage in README

### Risk: Brute Force Attacks

**Risk:** No rate limiting on authentication attempts enables brute force attacks on dashboard password.

**Mitigation:**
- Internal network deployment (firewall blocks external access)
- Fail2ban or similar can be deployed at infrastructure level
- Future enhancement: Add simple rate limiting per IP (out of scope for this change)

### Risk: Plaintext Password in Memory

**Risk:** Dashboard password stored in plaintext in server memory could be extracted via memory dump.

**Mitigation:**
- Server runs as dedicated user with restricted permissions
- Root required for memory access
- If server is compromised to this level, attacker already has file access (password file)
- Future enhancement: Use ctypes to lock memory pages (overkill for current threat model)

### Risk: Token Rotation Requires Restart

**Risk:** Rotating tokens requires service restart, causing brief downtime.

**Mitigation:**
- Add multiple tokens to file (clients can use old token while new one is added)
- Restart is quick (~1 second)
- Health check enables zero-downtime deployment with load balancer
- Future enhancement: SIGHUP reload handler (out of scope for MVP)

### Risk: No Token Expiry

**Risk:** Tokens are valid indefinitely unless manually removed from file.

**Mitigation:**
- Operational policy: Review token file during audits
- If token compromised, remove from file and restart
- Future enhancement: Token expiry timestamps in YAML (out of scope for MVP)

### Trade-off: Breaking Change

**Trade-off:** Existing deployments will fail to start after update.

**Acceptance:**
- Documented as breaking change in proposal
- Migration path: Add auth files to deployment, then upgrade
- Better to break loudly than silently allow unauthenticated access

## Migration Plan

### Pre-Deployment

1. **Generate secrets** (outside Honeybadger scope):
   ```bash
   # Token generation (example - use your secret manager)
   echo "tokens:" > tokens.yaml
   echo "  - hb_$(openssl rand -hex 16)" >> tokens.yaml

   # Password generation
   openssl rand -base64 24 > password.txt
   ```

2. **Update systemd unit** (or equivalent):
   ```ini
   [Service]
   ExecStart=/usr/local/bin/honeybadger_server.py \
     --config /etc/honeybadger/config.yaml \
     --token-file /run/agenix/honeybadger-tokens.yaml \
     --dashboard-password-file /run/agenix/honeybadger-password.txt
   ```

3. **Update client scripts** (add Authorization header):
   ```bash
   curl -X POST http://server:7123/ \
     -H "Authorization: Bearer hb_abc123..." \
     -H "X-Hostname: $(hostname)" \
     -H "X-Report-Type: lynis" \
     -d @report.json
   ```

### Deployment

1. Deploy new `honeybadger_server.py` version
2. Restart service
3. Verify startup logs show "Loaded N tokens and dashboard password"
4. Test API submission with token
5. Test dashboard access in browser (should see login prompt)

### Rollback

If deployment fails:
1. Revert to previous `honeybadger_server.py` version
2. Remove auth file arguments from systemd unit
3. Restart service

**Note:** Old version won't validate auth files, so they can remain in place during rollback.

### Post-Deployment

1. Update README.md with authentication examples
2. Distribute tokens to client systems
3. Share dashboard password with team (via password manager)
4. Test report submission from each client

## Open Questions

**Q: Should we support multiple dashboard passwords for different users?**
**A:** No - out of scope. Single password sufficient for MVP. Future enhancement could add user table.

**Q: Should /health endpoint return statistics that could be sensitive?**
**A:** Current statistics (report counts, uptime) are not sensitive. If this changes, revisit auth exemption.

**Q: What happens if token file has duplicate tokens?**
**A:** Validation logic treats them as separate entries (no deduplication). Harmless but wasteful. Could add warning during load.
