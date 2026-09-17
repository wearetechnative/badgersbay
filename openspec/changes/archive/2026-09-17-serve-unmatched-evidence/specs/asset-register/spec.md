## MODIFIED Requirements

### Requirement: Report unmatched submissions

The system SHALL surface submissions that do not resolve to a register entry,
distinguishing a missing serial from a serial the register does not know, and
SHALL make the evidence behind each one reachable from that report.

#### Scenario: Unmatched submissions present
- **WHEN** one or more submissions in the open round are unmatched
- **THEN** the dashboard shows a warning block listing them with hostname,
  username, serial and upload time

#### Scenario: Reason recorded per submission
- **WHEN** a submission does not resolve
- **THEN** the record carries `no_serial` or `serial_not_in_register`

#### Scenario: Reasons reported separately
- **WHEN** the dashboard lists unmatched submissions
- **THEN** it groups them by reason, because a missing serial is a client
  problem and an unknown serial is a register problem

#### Scenario: Submission is never discarded
- **WHEN** a submission cannot be resolved for any reason
- **THEN** the archive and its extracted reports are stored, and the upload
  returns success

#### Scenario: Evidence is reachable from the reason
- **WHEN** an unmatched submission is listed under its reason
- **THEN** its stored reports and archive are linked beside it, because both
  reasons are settled by reading what the machine sent
