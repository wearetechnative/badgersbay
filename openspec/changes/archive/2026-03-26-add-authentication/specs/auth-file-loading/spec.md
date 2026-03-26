# Auth File Loading

## Overview

The server requires explicit CLI arguments for authentication files and loads them at startup. No fallback locations are supported - both files must be provided or the server fails to start.

## ADDED Requirements

### Requirement: CLI Arguments Required

The server SHALL require both `--token-file` and `--dashboard-password-file` CLI arguments to start.

#### Scenario: Server fails without token file
- **WHEN** server starts without `--token-file` argument
- **THEN** server exits with error "Missing required argument: --token-file" and exit code 1

#### Scenario: Server fails without password file
- **WHEN** server starts without `--dashboard-password-file` argument
- **THEN** server exits with error "Missing required argument: --dashboard-password-file" and exit code 1

#### Scenario: Server starts with both files
- **WHEN** server starts with `--token-file /path/to/tokens.yaml --dashboard-password-file /path/to/password.txt`
- **THEN** server loads both files and starts successfully

### Requirement: No Fallback Locations

The server SHALL NOT search for authentication files in fallback locations.

#### Scenario: No default file locations
- **WHEN** server starts with explicit file paths
- **THEN** server uses only the specified paths, never checks ./tokens.yaml or /etc/honeybadger/

#### Scenario: Relative paths supported
- **WHEN** server starts with `--token-file ./tokens.yaml`
- **THEN** server resolves path relative to working directory

#### Scenario: Absolute paths supported
- **WHEN** server starts with `--token-file /etc/honeybadger/tokens.yaml`
- **THEN** server uses absolute path as provided

### Requirement: File Existence Validation

The server SHALL validate that both authentication files exist before loading credentials.

#### Scenario: Token file not found
- **WHEN** server starts with `--token-file /nonexistent/tokens.yaml`
- **THEN** server exits with error "Token file not found: /nonexistent/tokens.yaml" and exit code 1

#### Scenario: Password file not found
- **WHEN** server starts with `--dashboard-password-file /nonexistent/password.txt`
- **THEN** server exits with error "Dashboard password file not found: /nonexistent/password.txt" and exit code 1

#### Scenario: Both files exist
- **WHEN** both specified files exist and are readable
- **THEN** server continues to content validation phase

### Requirement: File Readability Validation

The server SHALL validate that authentication files are readable before parsing content.

#### Scenario: Token file not readable
- **WHEN** token file exists but lacks read permission
- **THEN** server exits with error "Cannot read token file: <path>" and exit code 1

#### Scenario: Password file not readable
- **WHEN** password file exists but lacks read permission
- **THEN** server exits with error "Cannot read dashboard password file: <path>" and exit code 1

### Requirement: Load Order and Timing

The server SHALL load authentication files at startup before binding to network port.

#### Scenario: Files loaded before network binding
- **WHEN** server starts with valid auth files
- **THEN** server loads and validates files BEFORE opening listening socket

#### Scenario: Startup failure prevents network binding
- **WHEN** auth file loading fails
- **THEN** server exits without binding to port (no port already in use error on retry)

#### Scenario: In-memory storage only
- **WHEN** server successfully loads auth files
- **THEN** credentials stored in memory, files not read again during runtime

### Requirement: Fail-Fast Validation

The server SHALL validate all authentication configuration before starting HTTP server.

#### Scenario: All validation happens at startup
- **WHEN** server starts
- **THEN** server validates CLI args → file existence → file readability → file format → content validity in sequence

#### Scenario: First error stops startup
- **WHEN** any validation step fails
- **THEN** server exits immediately with descriptive error, does not continue to next validation

#### Scenario: Success message after validation
- **WHEN** all validation passes
- **THEN** server logs "Loaded N tokens and dashboard password" before starting HTTP server

### Requirement: Token File Format Validation

The server SHALL validate token file YAML structure at startup.

#### Scenario: Valid YAML with tokens list
- **WHEN** token file contains valid YAML with `tokens: [...]` structure
- **THEN** server parses and loads token list into memory

#### Scenario: Invalid YAML syntax
- **WHEN** token file contains malformed YAML
- **THEN** server exits with error showing YAML parse error and line number

#### Scenario: Missing tokens key
- **WHEN** token file is valid YAML but lacks `tokens:` key
- **THEN** server exits with error "Token file missing 'tokens' key" and exit code 1

#### Scenario: Empty tokens list
- **WHEN** token file contains `tokens: []`
- **THEN** server exits with error "Token file contains no tokens" and exit code 1

#### Scenario: Non-list tokens value
- **WHEN** token file contains `tokens: "string"` instead of list
- **THEN** server exits with error "Token file 'tokens' must be a list" and exit code 1

### Requirement: Password File Format Validation

The server SHALL validate password file content at startup.

#### Scenario: Valid password file
- **WHEN** password file contains non-empty text
- **THEN** server trims whitespace and loads password

#### Scenario: Empty password file
- **WHEN** password file exists but is empty or contains only whitespace
- **THEN** server exits with error "Dashboard password file is empty" and exit code 1

#### Scenario: Multi-line password file
- **WHEN** password file contains multiple lines
- **THEN** server uses only first line and logs warning "Dashboard password file contains multiple lines, using first line only"

### Requirement: CLI Help Documentation

The server SHALL document authentication arguments in `--help` output.

#### Scenario: Help shows required arguments
- **WHEN** user runs `./honeybadger_server.py --help`
- **THEN** output includes both authentication arguments marked as required

#### Scenario: Help explains file formats
- **WHEN** user runs `./honeybadger_server.py --help`
- **THEN** output describes token file format (YAML) and password file format (plaintext)

#### Scenario: Help shows example paths
- **WHEN** user runs `./honeybadger_server.py --help`
- **THEN** output includes example: `--token-file /etc/honeybadger/tokens.yaml --dashboard-password-file /etc/honeybadger/password.txt`

### Requirement: Error Message Quality

The server SHALL provide clear, actionable error messages for authentication file issues.

#### Scenario: Error includes file path
- **WHEN** file loading fails
- **THEN** error message includes the exact path that was attempted

#### Scenario: Error distinguishes file types
- **WHEN** token or password file fails
- **THEN** error message clearly identifies which file type failed (token vs password)

#### Scenario: Error suggests fix
- **WHEN** file not found
- **THEN** error message suggests checking path and file permissions

#### Scenario: YAML error shows line number
- **WHEN** token file has YAML syntax error
- **THEN** error message includes line number where parsing failed
