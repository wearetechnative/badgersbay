## Why

Currently, `honeybadger_server.py` searches for `config.yaml` only relative to the script's own location using `__file__`. This makes it difficult to use the server in containerized environments, systemd services, or when installed system-wide, where the config file should be in `/etc/`, a working directory, or a custom location. Users cannot override the config path without modifying the script.

## What Changes

- Add `--config` command line argument to specify custom config.yaml path
- Add fallback search order: CLI argument → current working directory → script directory → `/etc/honeybadger/config.yaml`
- Add `--version` and `--help` arguments for better CLI usability
- Maintain backward compatibility: existing deployments without CLI args continue to work
- Update startup logging to show which config file was loaded

## Capabilities

### New Capabilities
- `cli-arguments`: Command line argument parsing for server configuration (--config, --help, --version)

### Modified Capabilities
- `config-loading`: Update configuration loading to support multiple config file locations with fallback chain

## Impact

- **Code**: Adds argparse-based CLI argument handling in startup section
- **Configuration**: Adds flexible config file discovery (no breaking changes - existing behavior is default)
- **Deployment**: Enables standard deployment patterns (systemd, Docker, system-wide installation)
- **Backward Compatibility**: Fully compatible - users without CLI args see no change
- **Documentation**: README needs update with CLI argument examples
