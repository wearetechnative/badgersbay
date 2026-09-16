## ADDED Requirements

### Requirement: Show the audit's findings in the fleet view

The fleet view SHALL show the compliance values the client determined, so they
can be read off rather than reconstructed by hand.

#### Scenario: Findings shown
- **WHEN** an asset's latest submission carries an inventory
- **THEN** the row shows disk encryption, screen lock, firewall, hardening
  score and OS up-to-date

#### Scenario: A declined value reads as unknown with its reason
- **WHEN** a finding carries a null value and a populated finding text
- **THEN** the cell reads as unknown and the client's reason is available on
  the row

#### Scenario: An asset with no inventory
- **WHEN** the latest submission carries no inventory, as an older client or a
  Windows asset produces
- **THEN** the cells read as unknown rather than as a failure

#### Scenario: Provenance is available
- **WHEN** a value is shown
- **THEN** the finding it was derived from can be seen without opening the
  stored archive

#### Scenario: The dashboard adds no verdict
- **WHEN** findings are rendered
- **THEN** no value is coloured as pass or fail; the client's finding text
  carries its own verdict and the threshold belongs to the ISO process
