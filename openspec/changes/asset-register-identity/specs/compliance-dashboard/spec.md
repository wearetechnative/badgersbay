## ADDED Requirements

### Requirement: Round view

The system SHALL show progress of the currently open audit round against the
asset register.

#### Scenario: Every register entry is a row
- **WHEN** the register holds eleven assets and five have submitted in the open
  round
- **THEN** the view shows eleven rows and a progress count of 5 / 11

#### Scenario: Assets that have not submitted
- **WHEN** an asset has no submission in the open round
- **THEN** it appears as outstanding, with the date it was last seen in any
  round, or "never seen"

#### Scenario: Breakdown by owner
- **WHEN** the round view renders
- **THEN** it groups outstanding assets by owner, so that one owner holding
  several assets is a single point of contact

#### Scenario: Excused and retired assets
- **WHEN** a register entry has a status excluding it from the round
- **THEN** it is not counted in the denominator and is listed separately

### Requirement: Fleet view

The system SHALL show the latest known state of every asset regardless of audit
round.

#### Scenario: Latest submission per asset
- **WHEN** an asset submitted in both the 2026-03 and 2026-09 rounds
- **THEN** the fleet view shows the 2026-09 submission

#### Scenario: Freshness relative to the current round
- **WHEN** the fleet view renders
- **THEN** each asset is marked as covered in the open round, covered in the
  previous round only, or stale beyond that

#### Scenario: Asset never seen
- **WHEN** a register entry has no submission at all
- **THEN** it appears with "never seen" rather than being omitted
