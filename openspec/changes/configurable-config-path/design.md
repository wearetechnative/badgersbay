# Configurable Config Path - Design

## Context

Currently, `honeybadger_server.py` loads `config.yaml` using a hardcoded path relative to the script location:

```python
config_path = Path(__file__).parent / 'config.yaml'
```

This works for simple deployments where the script and config are in the same directory, but creates issues for:
- **Systemd services**: Config files should be in `/etc/`
- **Docker containers**: Config mounted as volume at standard location
- **System-wide installation**: Script in `/usr/local/bin/`, config in `/etc/`
- **Multiple instances**: Different working directories with per-instance configs

The server uses Python's standard library exclusively (no external dependencies beyond PyYAML), and we want to maintain this simplicity.

## Goals / Non-Goals

**Goals:**
- Add `--config` CLI argument to explicitly specify config path
- Implement fallback search order for flexibility
- Maintain 100% backward compatibility with existing deployments
- Use only Python stdlib (argparse) - no new dependencies
- Add `--version` and `--help` for standard CLI UX

**Non-Goals:**
- Environment variable support (can be added later if needed)
- Complex config merging from multiple files
- Config validation beyond existing checks
- Config file generation/initialization wizard

## Decisions

### Decision 1: Use argparse for CLI argument parsing

**Rationale:** Python's built-in argparse provides standard CLI behavior (--help, --version, error handling) with zero dependencies.

**Alternatives considered:**
- Manual sys.argv parsing: More brittle, no automatic help generation
- Click/typer library: Adds external dependency, overkill for simple use case

**Decision:** Use argparse. It's stdlib, well-documented, and provides exactly what we need.

### Decision 2: Config file search order

**Order:**
1. CLI argument (`--config /path/to/config.yaml`)
2. Working directory (`./config.yaml`)
3. Script directory (`<script-dir>/config.yaml`)
4. System-wide (`/etc/honeybadger/config.yaml`)

**Rationale:**
- CLI argument highest priority (explicit user intent)
- Working directory second (enables per-instance configs without CLI args)
- Script directory third (maintains backward compatibility)
- System location last (standard Unix convention)

**Alternatives considered:**
- Script directory first: Would break per-instance configs use case
- Only CLI argument: Forces all users to update deployment scripts
- Environment variable: Added complexity, less discoverable than CLI arg

**Decision:** Implement full fallback chain. Provides maximum flexibility while maintaining backward compatibility.

### Decision 3: Path resolution for --config argument

**Rationale:** Relative paths should resolve from current working directory (not script directory), as this matches user expectations and standard tool behavior.

**Implementation:**
```python
if args.config:
    config_path = Path(args.config).expanduser().resolve()
else:
    # Search fallback locations
```

**Decision:** Use `expanduser()` to support `~/` paths and `resolve()` to convert to absolute path.

### Decision 4: Error handling and exit codes

**Exit codes:**
- 0: Success
- 1: Config file error (not found, invalid YAML, missing fields)
- 2: CLI argument error (invalid argument, argparse default)

**Rationale:** Standard Unix exit code conventions. Non-zero indicates error type for scripting.

**Decision:** Fail fast with clear error messages. List all searched locations when config not found.

### Decision 5: Version number storage

**Options:**
- Hardcode in script
- Read from VERSION file
- Read from git tag

**Decision:** Hardcode as constant at top of script. Simple, no file I/O, sufficient for single-file app.

```python
VERSION = "1.0.0"
```

Can be updated to read from file later if needed for automated releases.

## Risks / Trade-offs

### Risk: Working directory config takes precedence over script directory
**Impact:** If user has stale `config.yaml` in working directory, it will be used instead of intended config in script directory.
**Mitigation:** Log which config file is loaded at startup. Clear documentation about search order. Most users won't have multiple config files.

### Risk: Path expansion behavior differences across platforms
**Impact:** `expanduser()` behavior may differ on Windows vs Unix.
**Mitigation:** Use `Path.expanduser()` and `Path.resolve()` which handle platform differences. Document behavior.

### Trade-off: Increased startup complexity
**Impact:** More code to maintain, more failure modes.
**Benefit:** Much more flexible deployment. Worth the complexity for improved usability.

### Trade-off: No environment variable support
**Impact:** Some users may expect `HONEYBADGER_CONFIG` env var.
**Mitigation:** Can be added later without breaking changes. CLI argument covers 90% of use cases.

## Migration Plan

### Deployment Steps

1. **Add argparse import and CLI parsing**
   - Import argparse at top of file
   - Define argument parser with --config, --version, --help
   - Parse arguments before config loading

2. **Add VERSION constant**
   - Define at top of file (e.g., VERSION = "1.0.0")

3. **Refactor config loading**
   - Extract current config loading into `find_config_file()` function
   - Implement fallback search logic
   - Return tuple: (config_path, Config) or exit on error

4. **Update logging**
   - Log which config file was loaded: "Configuration loaded from /path/to/config.yaml"
   - Include searched locations in error message

5. **Update documentation**
   - Add CLI arguments section to README
   - Add deployment examples (systemd, Docker)
   - Update CLAUDE.md with new behavior

6. **Testing**
   - Test each fallback location
   - Test --config with absolute/relative paths
   - Test error cases (missing file, invalid YAML)
   - Test backward compatibility (no CLI args)

### Rollback Strategy

No data migration needed. Rollback is simple:
- Revert to previous version of script
- Existing deployments unaffected (they don't use CLI args)

If issues found:
- Can disable working directory search temporarily
- Can simplify to just CLI argument + script directory

### Backward Compatibility

**Guaranteed:**
- Existing deployments with `config.yaml` in script directory continue to work unchanged
- No CLI arguments required
- No changes to config file format

**Test scenario:**
```bash
# Old deployment (no changes)
./honeybadger_server.py
# Should load ./config.yaml (script directory) and work exactly as before
```

## Open Questions

None at this time. Design is ready for implementation.
