# Implementation Tasks

## 1. Add CLI Argument Support

- [x] 1.1 Add `import argparse` at top of honeybadger_server.py
- [x] 1.2 Define VERSION constant at top of file (e.g., VERSION = "1.0.0")
- [x] 1.3 Create `parse_arguments()` function that returns parsed args
- [x] 1.4 Add `--config` argument with metavar, help text, and type=str
- [x] 1.5 Add `--version` argument that prints version and exits
- [x] 1.6 Add `-h/--help` argument (automatic from argparse)
- [x] 1.7 Set argparse program name and description

## 2. Implement Config File Discovery

- [x] 2.1 Create `find_config_file(cli_config_path)` function
- [x] 2.2 If cli_config_path provided, expand user (~) and resolve to absolute path
- [x] 2.3 If cli_config_path provided and exists, return it
- [x] 2.4 If cli_config_path provided but doesn't exist, exit with error and exit code 1
- [x] 2.5 Search working directory for config.yaml (Path.cwd() / 'config.yaml')
- [x] 2.6 Search script directory for config.yaml (Path(__file__).parent / 'config.yaml')
- [x] 2.7 Search /etc/honeybadger/config.yaml
- [x] 2.8 If no config found, exit with error listing all searched locations, exit code 1
- [x] 2.9 Return first found config path

## 3. Refactor Config Loading

- [x] 3.1 Update main startup code to call parse_arguments()
- [x] 3.2 Call find_config_file(args.config) before loading config
- [x] 3.3 Pass returned config_path to existing Config loading logic
- [x] 3.4 Add logging statement "Configuration loaded from {config_path}"
- [x] 3.5 Handle YAML parsing errors with clear error message and exit code 1
- [x] 3.6 Handle missing required fields with clear error message and exit code 1

## 4. Testing

- [x] 4.1 Test --help displays all arguments and usage information
- [x] 4.2 Test --version displays version string and exits
- [x] 4.3 Test --config with absolute path loads correct file
- [x] 4.4 Test --config with relative path resolves from working directory
- [x] 4.5 Test --config with ~ (tilde) expands to home directory
- [x] 4.6 Test --config with nonexistent file exits with error
- [x] 4.7 Test fallback to working directory config.yaml
- [x] 4.8 Test fallback to script directory config.yaml (backward compatibility)
- [x] 4.9 Test fallback to /etc/honeybadger/config.yaml
- [x] 4.10 Test error when no config found anywhere
- [x] 4.11 Test invalid YAML syntax shows clear error
- [x] 4.12 Test working directory config takes precedence over script directory
- [x] 4.13 Test CLI config takes precedence over all fallbacks
- [x] 4.14 Verify backward compatibility: no CLI args, config in script dir works

## 5. Documentation

- [x] 5.1 Add CLI Arguments section to README.md with examples
- [x] 5.2 Document config file search order in README.md
- [x] 5.3 Add systemd service example with --config in README.md
- [x] 5.4 Add Docker example with config volume mount in README.md
- [x] 5.5 Update CLAUDE.md to document CLI arguments and config search behavior
