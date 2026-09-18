# Tasks

## 1. Confirm no code depends on the old rule

- [x] 1.1 Read `AssetRegister.load()`, `_parse_row()` and
      `_check_serial_overlaps()` and record what is actually validated
- [x] 1.2 Grep `honeybadger_server.py` for the old rule's wording - issuer,
      registrar, the ISO tool as the source of `asset_id`

## 2. The specification

- [x] 2.1 REMOVED block for "Where the durable identity comes from", with a
      `**Reason**:` and a `**Migration**:` line
- [x] 2.2 ADDED requirement: the register is the record of asset identity
- [x] 2.3 Keep the two scenarios that survive - identity follows the asset, and
      several serials over one asset's life
- [x] 2.4 Add how a new asset gets a number, and that divergence from the ISO
      tool is expected
- [x] 2.5 State what the loader does not check, so no enforcement is implied

## 3. Verify

- [x] 3.1 `python3 -m doctest honeybadger_server.py`
- [x] 3.2 `python3 -m unittest test_asset_inventory`
- [x] 3.3 `openspec validate --strict` and `openspec validate --specs --strict`
- [x] 3.4 Sync the delta into `openspec/specs/asset-register/spec.md`
- [x] 3.5 CHANGELOG entry under `## NEXT VERSION`
