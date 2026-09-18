# The register is where asset identity lives

## Why

The xlsx export out of the ISO tool was a one-off. It was used once, to get the
asset list in order, and it is not a feed. The register in badgersbay is the
working list now, and it is where asset identities are maintained. That has been
decided.

The specification says the opposite. `asset-register` carries a requirement
called "Where the durable identity comes from" which states that `asset_id`
SHALL be the identifier the ISO tool assigns and that badgersbay SHALL NOT issue
identifiers of its own, with a scenario titled "The register is not the
registrar" arguing that two issuers would drift.

It was already untrue when it was written. `TARI-00022` (`PF50L2ML`, Mathijs van
Veluw) and `TARI-00041` (`MP1Y69AC`, Pim Snel) were assigned by hand during the
rebuild and exist only in this register; `badgersbay-kgl2` asked for both to be
recorded in the tool precisely because the tool and the register had already
diverged. A requirement that contradicts what is actually done is worse than no
requirement, because it is read as the rule by whoever comes next.

## What Changes

- The requirement "Where the durable identity comes from" is removed, with its
  reason and a migration line, rather than modified. Keeping the name over a
  reversed meaning would hide that the old rule was wrong
- A requirement replaces it: the register is the record of asset identity.
  `asset_id` is assigned and maintained here, a number is never reused once
  issued, and two rows may share an `asset_id` only as the serial history of one
  asset over time
- The two scenarios from the old requirement that are still true travel with it:
  identity follows the asset rather than the person holding it, and one asset
  may carry several serials over its life, distinguished by validity windows
- What the decision adds: how a new asset gets a number, and that divergence
  from the ISO tool is expected rather than a fault
- What the loader does not check is stated in the requirement itself, so the
  rule is not read as a validation the service performs

## Impact

- Affected specs: `asset-register`
- Affected code: none

## Not changed

No code. The identity rule was never enforced anywhere: `AssetRegister` reads
`asset_id`, refuses an empty one, and never looks at it again. Nothing in
`honeybadger_server.py` names the ISO tool as the issuer either - its remaining
mentions of the tool are about deviations being justified there, which is
unaffected. Verified by reading `AssetRegister.load()`, `_parse_row()` and
`_check_serial_overlaps()`, and by grepping the module for the old rule's
wording.

The Purpose of `asset-register` and the "Load asset register" requirement still
describe the register as exported from the ISO reporting sheet. That is how the
current file was produced and is left standing; it is a statement about where
the list came from, not about who issues identities.
