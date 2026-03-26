# API Authentication

## Overview

The server requires valid Bearer tokens for all report submission endpoints to prevent unauthorized data uploads.

## ADDED Requirements

### Requirement: Bearer Token Validation

The server SHALL validate Bearer tokens in the Authorization header for all POST requests to report submission endpoints.

#### Scenario: Valid token allows submission
- **WHEN** client sends POST request with `Authorization: Bearer hb_valid_token`
- **THEN** server validates token and processes the request normally

#### Scenario: Invalid token returns 401
- **WHEN** client sends POST request with `Authorization: Bearer hb_invalid_token`
- **THEN** server responds with HTTP 401 Unauthorized and error message

#### Scenario: Missing Authorization header returns 401
- **WHEN** client sends POST request without Authorization header
- **THEN** server responds with HTTP 401 Unauthorized and error message

#### Scenario: Malformed Authorization header returns 401
- **WHEN** client sends POST request with `Authorization: NotBearer token` (wrong format)
- **THEN** server responds with HTTP 401 Unauthorized and error message

### Requirement: Token Format

The server SHALL only accept tokens in the format `Authorization: Bearer <token>` following RFC 6750.

#### Scenario: Correct Bearer format accepted
- **WHEN** client sends `Authorization: Bearer hb_abc123`
- **THEN** server extracts token and validates it

#### Scenario: Custom header format rejected
- **WHEN** client sends `X-Api-Token: hb_abc123` instead of Authorization header
- **THEN** server responds with HTTP 401 Unauthorized

#### Scenario: Basic Auth format rejected
- **WHEN** client sends `Authorization: Basic base64data` to API endpoint
- **THEN** server responds with HTTP 401 Unauthorized (wrong auth type for API)

### Requirement: Token List Loading

The server SHALL load valid tokens from YAML file specified by `--token-file` CLI argument at startup.

#### Scenario: Load tokens from valid YAML file
- **WHEN** server starts with `--token-file /path/to/tokens.yaml` containing valid YAML
- **THEN** server loads all tokens from the file into memory

#### Scenario: Fail on missing token file
- **WHEN** server starts with `--token-file /nonexistent/tokens.yaml`
- **THEN** server exits with error "Token file not found" and exit code 1

#### Scenario: Fail on invalid YAML
- **WHEN** server starts with token file containing invalid YAML syntax
- **THEN** server exits with error showing YAML parse error and exit code 1

#### Scenario: Fail on empty token list
- **WHEN** server starts with token file containing `tokens: []` (empty list)
- **THEN** server exits with error "Token file contains no tokens" and exit code 1

### Requirement: Token File Format

The token file SHALL be YAML format with a `tokens` key containing a list of token strings.

#### Scenario: Standard token file format
- **WHEN** token file contains:
  ```yaml
  tokens:
    - hb_abc123
    - hb_xyz789
  ```
- **THEN** server loads both tokens as valid

#### Scenario: Whitespace handling
- **WHEN** token file contains tokens with leading/trailing whitespace
- **THEN** server trims whitespace and loads clean tokens

### Requirement: Protected Endpoints

The server SHALL require Bearer token authentication for all endpoints that accept report data.

#### Scenario: POST / requires token
- **WHEN** client sends POST to `/` without valid token
- **THEN** server responds with HTTP 401

#### Scenario: POST /submit-tar requires token
- **WHEN** client sends POST to `/submit-tar` without valid token
- **THEN** server responds with HTTP 401

#### Scenario: GET endpoints not affected
- **WHEN** client sends GET request (dashboard access uses different auth)
- **THEN** Bearer token is not checked (dashboard uses password auth)

### Requirement: Error Response Format

The server SHALL return clear error messages for authentication failures.

#### Scenario: Missing token error message
- **WHEN** POST request has no Authorization header
- **THEN** response body contains `{"error": "Missing Authorization header"}`

#### Scenario: Invalid token error message
- **WHEN** POST request has invalid token
- **THEN** response body contains `{"error": "Invalid authentication token"}`

#### Scenario: Malformed header error message
- **WHEN** Authorization header doesn't match "Bearer <token>" format
- **THEN** response body contains `{"error": "Invalid Authorization header format. Expected: Bearer <token>"}`
