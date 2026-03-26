# Dashboard Authentication

## Overview

The server requires HTTP Basic Authentication for accessing the web dashboard to prevent unauthorized viewing of compliance data.

## ADDED Requirements

### Requirement: Basic Auth Validation

The server SHALL validate HTTP Basic Authentication credentials for all GET requests to the dashboard.

#### Scenario: Valid password allows dashboard access
- **WHEN** browser sends GET to `/` with correct Basic Auth credentials
- **THEN** server validates password and serves dashboard HTML

#### Scenario: Invalid password returns 401
- **WHEN** browser sends GET to `/` with incorrect Basic Auth credentials
- **THEN** server responds with HTTP 401 Unauthorized and WWW-Authenticate header

#### Scenario: Missing credentials returns 401
- **WHEN** browser sends GET to `/` without Authorization header
- **THEN** server responds with HTTP 401 Unauthorized and WWW-Authenticate header

#### Scenario: Browser shows login prompt
- **WHEN** browser receives 401 with `WWW-Authenticate: Basic realm="Honeybadger Dashboard"`
- **THEN** browser displays built-in login dialog

### Requirement: Password File Loading

The server SHALL load dashboard password from plaintext file specified by `--dashboard-password-file` CLI argument at startup.

#### Scenario: Load password from valid file
- **WHEN** server starts with `--dashboard-password-file /path/to/password.txt`
- **THEN** server loads password into memory for validation

#### Scenario: Fail on missing password file
- **WHEN** server starts with `--dashboard-password-file /nonexistent/password.txt`
- **THEN** server exits with error "Dashboard password file not found" and exit code 1

#### Scenario: Fail on empty password file
- **WHEN** password file exists but contains only whitespace or is empty
- **THEN** server exits with error "Dashboard password file is empty" and exit code 1

### Requirement: Password File Format

The password file SHALL contain plaintext password (no YAML, no structure).

#### Scenario: Single line password
- **WHEN** password file contains `my_secure_password_123\n`
- **THEN** server loads and trims to `my_secure_password_123`

#### Scenario: Whitespace trimming
- **WHEN** password file contains `  my_password  \n`
- **THEN** server trims to `my_password`

#### Scenario: Multi-line rejected
- **WHEN** password file contains multiple lines
- **THEN** server uses only first line and logs warning

### Requirement: Basic Auth Header Format

The server SHALL accept HTTP Basic Auth in standard format following RFC 7617.

#### Scenario: Standard Basic Auth format
- **WHEN** request contains `Authorization: Basic <base64(username:password)>`
- **THEN** server decodes and validates password (username ignored)

#### Scenario: Username ignored
- **WHEN** client sends `Authorization: Basic <base64(admin:correct_password)>`
- **THEN** server validates only the password part, ignores username

#### Scenario: Bearer token rejected on dashboard
- **WHEN** client sends `Authorization: Bearer <token>` to dashboard endpoint
- **THEN** server responds with HTTP 401 (wrong auth type for dashboard)

### Requirement: Protected Dashboard Endpoints

The server SHALL require Basic Auth for all dashboard-related GET endpoints.

#### Scenario: GET / requires password
- **WHEN** browser accesses `/` without valid password
- **THEN** server responds with HTTP 401

#### Scenario: GET /status requires password
- **WHEN** browser accesses `/status` without valid password
- **THEN** server responds with HTTP 401

#### Scenario: GET /reports/<path> requires password
- **WHEN** browser tries to download report without valid password
- **THEN** server responds with HTTP 401

#### Scenario: POST endpoints not affected
- **WHEN** client sends POST request (API uses Bearer token auth)
- **THEN** Basic Auth password is not checked (API uses token auth)

### Requirement: Health Endpoint Exception

The server SHALL allow unauthenticated access to the `/health` endpoint for monitoring.

#### Scenario: Health endpoint accessible without auth
- **WHEN** monitoring system requests GET `/health`
- **THEN** server returns health status without requiring authentication

### Requirement: WWW-Authenticate Header

The server SHALL include proper WWW-Authenticate header in 401 responses to trigger browser login dialog.

#### Scenario: WWW-Authenticate header on 401
- **WHEN** unauthenticated request is made to dashboard
- **THEN** response includes `WWW-Authenticate: Basic realm="Honeybadger Dashboard"`

#### Scenario: Browser login dialog
- **WHEN** browser receives 401 with WWW-Authenticate header
- **THEN** browser displays native login dialog with username and password fields

### Requirement: Session Management

The server SHALL rely on browser's built-in Basic Auth session management (no server-side sessions).

#### Scenario: Browser caches credentials
- **WHEN** user successfully logs in via Basic Auth
- **THEN** browser automatically includes credentials in subsequent requests

#### Scenario: Logout via browser
- **WHEN** user wants to log out
- **THEN** user must use browser's "forget password" or close browser (server has no logout endpoint)
