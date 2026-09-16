## ADDED Requirements

### Requirement: Mark an asset as excepted for a round

The system SHALL allow an operator to record that an asset cannot be scanned in
the open round, with a required reason.

#### Scenario: Exception recorded
- **WHEN** an operator marks TARI-00031 as excepted for 2026-09 with a reason
- **THEN** the system stores `asset_id`, `audit_period`, `reason`, `marked_by`
  and `marked_at` under `reports/exceptions/2026-09/`

#### Scenario: Reason required
- **WHEN** an operator submits an exception with an empty or whitespace-only
  reason
- **THEN** the system rejects it and no exception is recorded

#### Scenario: Exception withdrawn
- **WHEN** an operator withdraws an exception
- **THEN** the asset returns to outstanding in the round view

#### Scenario: Exception survives an index rebuild
- **WHEN** the server restarts and rebuilds its index
- **THEN** previously recorded exceptions are loaded from disk

### Requirement: Exceptions are scoped to one round

An exception SHALL apply only to the audit period it was recorded for.

#### Scenario: Exception does not carry over
- **WHEN** an asset was excepted in 2026-09 and the 2027-03 round opens
- **THEN** the asset is outstanding in the new round with no exception

#### Scenario: Independent per round
- **WHEN** an asset is excepted in 2026-09 and scanned in 2026-03
- **THEN** both facts stand, each against its own round

### Requirement: A submission supersedes an exception

The system SHALL count a submission received for an excepted asset and SHALL
treat the exception as lapsed.

#### Scenario: Excepted asset submits after all
- **WHEN** TARI-00031 is excepted for 2026-09 and then submits within that round
- **THEN** the asset counts as scanned and no longer as excepted

#### Scenario: No manual withdrawal needed
- **WHEN** a submission supersedes an exception
- **THEN** the round view reflects it without operator action

### Requirement: Validate the delivered register

The system SHALL validate the register it is given at startup and SHALL report
assets that disappeared relative to the previously loaded one.

#### Scenario: Invalid register refuses startup
- **WHEN** the delivered register contains a duplicate active serial, an unknown
  platform class, or overlapping validity windows for one serial
- **THEN** the service refuses to start with an error naming the fault

#### Scenario: Shrinking register is reported, not blocked
- **WHEN** the delivered register holds fewer assets than the previously loaded
  one
- **THEN** the service starts and reports the disappeared assets prominently on
  the dashboard

#### Scenario: Register is not writable from the browser
- **WHEN** any request attempts to replace the asset register over HTTP
- **THEN** the request is refused; the register is delivered as a secret file

#### Scenario: Replacement does not move a frozen round
- **WHEN** the register is replaced while a round is open
- **THEN** that round continues to compute against its frozen copy
