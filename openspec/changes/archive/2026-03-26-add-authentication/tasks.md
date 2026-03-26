# Implementation Tasks

## 1. CLI Arguments and Startup Validation

- [x] 1.1 Add `--token-file` argument to argparse with required=True
- [x] 1.2 Add `--dashboard-password-file` argument to argparse with required=True
- [x] 1.3 Update `--help` text to document both arguments with examples
- [x] 1.4 Test that server exits with clear error when arguments are missing

## 2. Credential Loading Functions

- [x] 2.1 Create `load_token_file()` function to parse YAML and extract token list
- [x] 2.2 Add validation for YAML structure (must have 'tokens' key as list)
- [x] 2.3 Add validation for empty token list (fail with error)
- [x] 2.4 Add whitespace trimming for tokens
- [x] 2.5 Create `load_password_file()` function to read plaintext password
- [x] 2.6 Add validation for empty password file (fail with error)
- [x] 2.7 Add first-line extraction and warning for multi-line files
- [x] 2.8 Add whitespace trimming for password
- [x] 2.9 Test both functions with valid and invalid input files

## 3. Startup Sequence

- [x] 3.1 Add global variables `VALID_TOKENS` (list) and `DASHBOARD_PASSWORD` (string)
- [x] 3.2 Call credential loading functions before server.serve_forever()
- [x] 3.3 Add try/except to catch file not found errors with descriptive messages
- [x] 3.4 Add try/except to catch YAML parse errors with line numbers
- [x] 3.5 Add try/except to catch permission errors with descriptive messages
- [x] 3.6 Add success log message showing loaded token count
- [x] 3.7 Test startup failure scenarios (missing files, invalid YAML, empty files)
- [x] 3.8 Verify server doesn't bind to port if credential loading fails

## 4. Bearer Token Validation for API

- [x] 4.1 Import `secrets` module for constant-time comparison
- [x] 4.2 Create `_validate_bearer_token()` method in RequestHandler
- [x] 4.3 Extract Authorization header and check for "Bearer " prefix
- [x] 4.4 Extract token from header (remove "Bearer " prefix)
- [x] 4.5 Compare token against VALID_TOKENS using secrets.compare_digest()
- [x] 4.6 Return True if match found, False otherwise
- [x] 4.7 Test with valid token, invalid token, missing header, malformed header

## 5. Basic Auth Validation for Dashboard

- [x] 5.1 Import `base64` module for header decoding
- [x] 5.2 Create `_validate_basic_auth()` method in RequestHandler
- [x] 5.3 Extract Authorization header and check for "Basic " prefix
- [x] 5.4 Decode base64 credentials with error handling
- [x] 5.5 Split decoded string on first ":" to extract username and password
- [x] 5.6 Compare password against DASHBOARD_PASSWORD using secrets.compare_digest()
- [x] 5.7 Ignore username field (don't validate)
- [x] 5.8 Test with valid password, invalid password, missing header, malformed header

## 6. POST Endpoint Protection

- [x] 6.1 Add auth check at start of do_POST() method
- [x] 6.2 Call _validate_bearer_token() and return 401 if False
- [x] 6.3 Create `_send_auth_error()` helper to send JSON error response
- [x] 6.4 Set WWW-Authenticate header to reject Basic Auth on API endpoints
- [x] 6.5 Test POST to / without token (should get 401)
- [x] 6.6 Test POST to / with invalid token (should get 401)
- [x] 6.7 Test POST to / with valid token (should process normally)
- [x] 6.8 Test POST to /submit-tar without token (should get 401)
- [x] 6.9 Test POST to /submit-tar with valid token (should process normally)

## 7. GET Endpoint Protection

- [x] 7.1 Add auth check at start of do_GET() method after /health check
- [x] 7.2 Skip auth for /health endpoint (early return)
- [x] 7.3 Call _validate_basic_auth() and return 401 if False
- [x] 7.4 Set WWW-Authenticate header with realm="Honeybadger Dashboard"
- [x] 7.5 Send HTML body for 401 response (browser-friendly)
- [x] 7.6 Test GET / without auth (should get 401 with login prompt)
- [x] 7.7 Test GET / with invalid password (should get 401)
- [x] 7.8 Test GET / with valid password (should show dashboard)
- [x] 7.9 Test GET /status with valid password (should work)
- [x] 7.10 Test GET /reports/<path> with valid password (should download)
- [x] 7.11 Test GET /health without auth (should work - unauthenticated)

## 8. Error Response Format

- [x] 8.1 Create `_send_json_error(code, message)` helper for API endpoints
- [x] 8.2 Set Content-Type: application/json for API errors
- [x] 8.3 Send {"error": "message"} format for API 401 responses
- [x] 8.4 Create `_send_html_error(code, message)` helper for dashboard endpoints
- [x] 8.5 Set Content-Type: text/html for dashboard errors
- [x] 8.6 Include WWW-Authenticate header in dashboard 401 responses
- [x] 8.7 Test that browser shows native login dialog on 401
- [x] 8.8 Test that API clients get parseable JSON errors

## 9. Integration Testing

- [x] 9.1 Create sample tokens.yaml file with 2 tokens
- [x] 9.2 Create sample password.txt file with test password
- [x] 9.3 Start server with --token-file and --dashboard-password-file arguments
- [x] 9.4 Test full report submission workflow with curl and valid token
- [x] 9.5 Test dashboard access in browser with valid password
- [x] 9.6 Test browser login prompt appears on first visit
- [x] 9.7 Test browser caches credentials for subsequent requests
- [x] 9.8 Test /health endpoint works without authentication
- [x] 9.9 Verify all 4 report types (Lynis, Trivy, Vulnix, Neofetch) can be submitted
- [x] 9.10 Verify dashboard shows submitted reports correctly

## 10. Documentation

- [x] 10.1 Update README.md "Quick Start" section with auth file requirements
- [x] 10.2 Add "Authentication" section to README.md
- [x] 10.3 Document token file format (YAML) with example
- [x] 10.4 Document password file format (plaintext) with example
- [x] 10.5 Update CLI arguments section with auth flags
- [x] 10.6 Update "Submitting Reports" examples to include Authorization header
- [x] 10.7 Add curl examples for authenticated API requests
- [x] 10.8 Add browser authentication instructions for dashboard
- [x] 10.9 Document deployment changes (systemd unit file example)
- [x] 10.10 Add "Breaking Changes" section explaining migration from unauthenticated version
- [x] 10.11 Update CLAUDE.md with authentication architecture notes

## 11. Edge Cases and Cleanup

- [x] 11.1 Test token file with duplicate tokens (should work, warn if desired)
- [x] 11.2 Test password file with trailing newlines (should be trimmed)
- [x] 11.3 Test password file with leading/trailing spaces (should be trimmed)
- [x] 11.4 Test token file with empty string tokens (should fail validation)
- [x] 11.5 Test relative paths for auth files (should resolve from working directory)
- [x] 11.6 Test absolute paths for auth files (should work)
- [x] 11.7 Verify no Authorization headers are logged (security)
- [x] 11.8 Verify error messages don't leak password/token values
- [x] 11.9 Test token rotation by restarting with updated tokens.yaml
- [x] 11.10 Verify old reports (pre-auth) are still accessible after upgrade
