## MODIFIED Requirements

### Requirement: Round view

The system SHALL show progress of the currently open audit round against the
asset register, in three categories: scanned, excepted and outstanding.

#### Scenario: Every register entry is a row
- **WHEN** the register holds eleven assets and five have submitted in the open
  round
- **THEN** the view shows eleven rows and a progress count of 5 / 11

#### Scenario: Three-category progress
- **WHEN** eight assets have submitted, two are excepted and one is outstanding
- **THEN** the view reports "8 scanned, 2 excepted, 1 outstanding" and does not
  present excepted assets as scanned

#### Scenario: Round closeable
- **WHEN** no assets remain outstanding
- **THEN** the round is reported as closeable, with the number of exceptions
  shown alongside

#### Scenario: Assets that have not submitted
- **WHEN** an asset has no submission in the open round and no exception
- **THEN** it appears as outstanding, with the date it was last seen in any
  round, or "never seen"

#### Scenario: Breakdown by owner
- **WHEN** the round view renders
- **THEN** it groups outstanding assets by owner, so that one owner holding
  several assets is a single point of contact

#### Scenario: Excused and retired assets
- **WHEN** a register entry has a status excluding it from the round
- **THEN** it is not counted in the denominator and is listed separately

## ADDED Requirements

### Requirement: Exception control

The system SHALL offer a control on the round view for marking an outstanding
asset as excepted, and SHALL show the recorded detail.

#### Scenario: Control present on outstanding rows
- **WHEN** an asset is outstanding in the open round
- **THEN** the row offers a control to mark it excepted, with a reason field

#### Scenario: Recorded detail shown
- **WHEN** an asset is excepted
- **THEN** the row shows the reason, who marked it and when

#### Scenario: Attribution labelled as self-reported
- **WHEN** the dashboard displays who marked an exception
- **THEN** it labels the value as self-reported, because the dashboard uses a
  single shared password

#### Scenario: Control requires dashboard authentication
- **WHEN** an unauthenticated request posts an exception
- **THEN** the request is rejected with 401
