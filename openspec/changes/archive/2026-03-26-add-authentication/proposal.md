## Why

The Honeybadger server is **internet-facing** and currently has no authentication. Anyone can POST reports (data pollution risk) or view the compliance dashboard (exposing sensitive audit data). This creates unacceptable security risks for production deployment.

## What Changes

- **BREAKING**: Add mandatory authentication - server fails to start without auth configuration
- Add `--token-file` CLI argument (required) for API token list (YAML format)
- Add `--dashboard-password-file` CLI argument (required) for dashboard password (plaintext)
- Validate `Authorization: Bearer <token>` header on all POST requests (401 if invalid)
- Validate HTTP Basic Auth on dashboard GET requests (401 if invalid)
- Load auth files at startup, keep in memory for validation
- No fallback locations - both files must be explicitly specified via CLI
- No token/password management UI - external tools (Nix/agenix) handle secret generation

## Capabilities

### New Capabilities
- `api-authentication`: Token-based authentication for report submission endpoints
- `dashboard-authentication`: Password-based authentication for web dashboard access
- `auth-file-loading`: CLI arguments and file loading for authentication credentials

### Modified Capabilities

None - this adds new authentication layer without modifying existing report handling behavior.

## Impact

- **Code**: New CLI args, auth file loading, token/password validation middleware
- **Deployment**: **BREAKING CHANGE** - existing deployments will fail to start without auth files
- **Clients**: Must include `Authorization: Bearer <token>` header in POST requests
- **Dashboard users**: Must provide password via HTTP Basic Auth
- **Configuration**: Two new required files managed by deployment system (NixOS/agenix)
- **Dependencies**: No new external dependencies (uses stdlib only)
- **Documentation**: README and CLAUDE.md need auth examples, deployment instructions
