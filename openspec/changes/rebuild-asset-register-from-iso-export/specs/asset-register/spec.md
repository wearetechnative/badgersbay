## ADDED Requirements

### Requirement: What belongs in the register

The register SHALL hold the assets whose absence from a round is a finding
somebody can act on, and no others. An asset that nobody can scan, or that
nobody is accountable for, SHALL NOT be counted in the denominator.

#### Scenario: An asset that cannot run the audit
- **WHEN** an ISO asset is not an endpoint - a television, a printer, a network
  device, a phone
- **THEN** it is not in the register, because coverage is a statement about
  systems that can be scanned

#### Scenario: An asset assigned to nobody
- **WHEN** an asset is held in stock with no user assigned
- **THEN** it is not in the register, because there is nobody to ask and a
  permanently outstanding row teaches readers to ignore the dashboard

#### Scenario: An asset outside ISO scope
- **WHEN** an asset belongs to a department that does not fall under the ISO
  scope
- **THEN** it is not in the register, and the exclusion is recorded with its
  reason so that a reader comparing the register against the company's laptop
  count can tell a decision from an omission

#### Scenario: A class the register does not know
- **WHEN** a row carries a platform class outside the supported set
- **THEN** the service refuses to start, so an asset that cannot be assessed is
  never silently counted as compliant

### Requirement: Where the durable identity comes from

`asset_id` SHALL be the identifier the ISO tool assigns to the asset. badgersbay
SHALL NOT issue identifiers of its own.

#### Scenario: The register is not the registrar
- **WHEN** an asset has no identifier in the ISO tool
- **THEN** one is assigned there before the asset enters the register, rather
  than invented in the register - two issuers would drift, and the register is
  delivered as an encrypted secret that nobody can consult

#### Scenario: Identity follows the asset, not its holder
- **WHEN** an asset is reassigned from one person to another
- **THEN** it keeps its own identifier and the register records the new owner;
  it does not inherit the identifier of the machine it replaced for that person

#### Scenario: Several serials over one asset's life
- **WHEN** an asset's reported serial changes, as after a mainboard replacement
- **THEN** the identifier is unchanged and the serials are distinguished by
  their validity windows

### Requirement: The serial is what the machine reports

Where the ISO tool and the machine disagree about a serial, the register SHALL
carry what the machine reports, because that is the value an incoming
submission is matched on.

#### Scenario: A hostname fragment recorded as a serial
- **WHEN** the tool holds a value that is a fragment of the hostname rather than
  a hardware serial
- **THEN** the register carries the serial read from the hardware, and the
  correction is raised against the tool as well

#### Scenario: Decoration the machine does not report
- **WHEN** the tool writes a serial with separators the machine omits
- **THEN** the register carries the machine's spelling; where no machine has yet
  reported, the risk is recorded rather than resolved by guessing
