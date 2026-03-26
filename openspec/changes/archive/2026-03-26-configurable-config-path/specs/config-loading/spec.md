# Config Loading

## Overview

The server loads configuration from a YAML file using a fallback search order to support various deployment scenarios.

## ADDED Requirements

### Requirement: Config File Search Order

The server SHALL search for configuration files in the following order and use the first one found:

1. Path specified via `--config` CLI argument (if provided)
2. `config.yaml` in current working directory
3. `config.yaml` in script directory (same directory as honeybadger_server.py)
4. `/etc/honeybadger/config.yaml` (system-wide config)

#### Scenario: CLI argument takes precedence
- **WHEN** `--config /custom/config.yaml` is provided and `./config.yaml` exists in working directory
- **THEN** server loads `/custom/config.yaml` (CLI argument has highest priority)

#### Scenario: Working directory fallback
- **WHEN** no `--config` argument provided and `config.yaml` exists in current working directory
- **THEN** server loads `./config.yaml` from working directory

#### Scenario: Script directory fallback
- **WHEN** no `--config` argument, no `config.yaml` in working directory, but `config.yaml` exists in script directory
- **THEN** server loads `config.yaml` from script directory (legacy behavior)

#### Scenario: System-wide config fallback
- **WHEN** no `--config` argument, no `config.yaml` in working or script directory, but `/etc/honeybadger/config.yaml` exists
- **THEN** server loads `/etc/honeybadger/config.yaml`

#### Scenario: No config file found
- **WHEN** no configuration file found in any search location
- **THEN** server exits with error message listing all searched locations and exit code 1

### Requirement: Config Path Logging

The server SHALL log which configuration file was loaded at startup.

#### Scenario: Log loaded config path
- **WHEN** server successfully loads configuration
- **THEN** server logs message "Configuration loaded from /path/to/config.yaml"

#### Scenario: Log search locations on failure
- **WHEN** no configuration file found
- **THEN** error message includes all locations that were searched

### Requirement: Backward Compatibility

The server SHALL maintain backward compatibility with existing deployments that don't use CLI arguments.

#### Scenario: Existing deployment without changes
- **WHEN** server is started without CLI arguments and `config.yaml` exists in script directory (traditional location)
- **THEN** server behaves exactly as before, loading config from script directory

#### Scenario: Working directory takes precedence over script directory
- **WHEN** no CLI arguments provided, `config.yaml` exists in both working directory and script directory
- **THEN** server loads from working directory (enables per-instance configs)

### Requirement: Config File Validation

The server SHALL validate that the configuration file is valid YAML and contains required fields.

#### Scenario: Invalid YAML syntax
- **WHEN** configuration file contains invalid YAML syntax
- **THEN** server exits with error message indicating YAML parse error and line number, exit code 1

#### Scenario: Missing required fields
- **WHEN** configuration file is valid YAML but missing required fields (networkport, storage_location)
- **THEN** server exits with error message listing missing required fields, exit code 1

### Requirement: Absolute and Relative Paths

The server SHALL support both absolute and relative paths for `--config` argument.

#### Scenario: Absolute path provided
- **WHEN** server is started with `--config /etc/honeybadger/config.yaml`
- **THEN** server uses absolute path as-is

#### Scenario: Relative path resolved from working directory
- **WHEN** server is started with `--config ../configs/honeybadger.yaml`
- **THEN** server resolves path relative to current working directory (not script directory)

#### Scenario: Tilde expansion in path
- **WHEN** server is started with `--config ~/honeybadger/config.yaml`
- **THEN** server expands `~` to user's home directory
