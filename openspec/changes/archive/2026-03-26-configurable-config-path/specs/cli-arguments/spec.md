# CLI Arguments

## Overview

The server accepts command line arguments to control configuration and provide usage information.

## ADDED Requirements

### Requirement: Config File Path Argument

The server SHALL accept a `--config` argument to specify the path to the configuration file.

#### Scenario: Custom config path provided
- **WHEN** server is started with `./honeybadger_server.py --config /etc/honeybadger/config.yaml`
- **THEN** server loads configuration from `/etc/honeybadger/config.yaml`

#### Scenario: Relative config path
- **WHEN** server is started with `--config ../my-config.yaml`
- **THEN** server resolves path relative to current working directory

#### Scenario: Config file does not exist
- **WHEN** server is started with `--config /nonexistent/config.yaml`
- **THEN** server exits with error message "Configuration file not found: /nonexistent/config.yaml" and exit code 1

#### Scenario: Config file is not readable
- **WHEN** server is started with `--config` pointing to unreadable file (no permissions)
- **THEN** server exits with error message about permission denied and exit code 1

### Requirement: Version Information

The server SHALL accept a `--version` argument to display version information.

#### Scenario: Display version
- **WHEN** server is started with `./honeybadger_server.py --version`
- **THEN** server prints "honeybadger-server version X.Y.Z" and exits with code 0

### Requirement: Help Information

The server SHALL accept `-h` or `--help` arguments to display usage information.

#### Scenario: Display help with --help
- **WHEN** server is started with `./honeybadger_server.py --help`
- **THEN** server prints usage information including all available arguments and exits with code 0

#### Scenario: Display help with -h
- **WHEN** server is started with `./honeybadger_server.py -h`
- **THEN** server prints usage information including all available arguments and exits with code 0

### Requirement: Help Text Content

The help text SHALL include descriptions of all command line arguments and their usage.

#### Scenario: Help includes config argument
- **WHEN** user runs `--help`
- **THEN** output includes description of `--config` argument with example

#### Scenario: Help includes version argument
- **WHEN** user runs `--help`
- **THEN** output includes description of `--version` argument

#### Scenario: Help includes examples
- **WHEN** user runs `--help`
- **THEN** output includes usage examples for common scenarios

### Requirement: Invalid Argument Handling

The server SHALL reject invalid command line arguments with clear error messages.

#### Scenario: Unknown argument provided
- **WHEN** server is started with `./honeybadger_server.py --unknown-arg`
- **THEN** server prints error message about unrecognized argument and shows help text, exits with code 2

#### Scenario: Config argument without value
- **WHEN** server is started with `./honeybadger_server.py --config` (no path provided)
- **THEN** server prints error message "argument --config: expected one argument" and exits with code 2
