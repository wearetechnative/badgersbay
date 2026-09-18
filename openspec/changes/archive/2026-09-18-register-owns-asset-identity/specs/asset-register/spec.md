## REMOVED Requirements

### Requirement: Where the durable identity comes from

**Reason**: The ISO tool's xlsx export was read once, to get the asset list in
order, and it is not a feed this register follows. Requiring `asset_id` to come
from that tool made the register dependent on a source nobody maintains for it,
and it was already untrue in practice: `TARI-00022` and `TARI-00041` were
assigned by hand during the rebuild and exist only here. A requirement that
contradicts what is done is read as the rule by whoever comes next.

**Migration**: Replaced by "The register is the record of asset identity", which
keeps the two scenarios that survive the decision - identity follows the asset
rather than its holder, and one asset may carry several serials over its life -
and states where a new number comes from instead. Nothing on disk changes: the
identifiers already in `assets.csv` keep their meaning, including the two that
the ISO tool does not know.

## ADDED Requirements

### Requirement: The register is the record of asset identity

`asset_id` SHALL be assigned and maintained in this register. A number once
issued SHALL NOT be reused for another asset. Two rows MAY carry the same
`asset_id` only as the serial history of one asset over time.

#### Scenario: A new asset is given a number here
- **WHEN** an asset enters scope and carries no identifier yet
- **THEN** it is given the next number not already present in the register,
  recorded with its serial, owner and validity window, rather than waited on
  from anywhere else

#### Scenario: A number outlives the asset that held it
- **WHEN** an asset is retired or leaves scope
- **THEN** its number stays with it and is never issued to another asset, so a
  closed round keeps naming the same machines it named when it closed

#### Scenario: Identity follows the asset, not its holder
- **WHEN** an asset is reassigned from one person to another
- **THEN** it keeps its own identifier and the register records the new owner;
  it does not inherit the identifier of the machine it replaced for that person

#### Scenario: Several serials over one asset's life
- **WHEN** an asset's reported serial changes, as after a mainboard replacement
- **THEN** the identifier is unchanged and the serials are distinguished by
  their validity windows

#### Scenario: Divergence from the ISO tool is expected
- **WHEN** the ISO tool holds a different identifier for an asset, or none at
  all, as it does for `TARI-00022` and `TARI-00041`
- **THEN** the register's value stands and the difference is not a fault; that
  tool was a source read once, not a system this register is synchronised with

#### Scenario: The service does not enforce this
- **WHEN** a register is loaded in which a number has been reused, or two
  unrelated assets carry the same `asset_id`
- **THEN** it loads without complaint: the loader checks `asset_id` only for
  emptiness, and validates classes, statuses, dates and overlapping validity per
  serial. This requirement is a discipline the register's maintainer keeps, and
  is written down here so that the absence of a check is visible rather than
  assumed
