## ADDED Requirements

### Requirement: Record the audit's findings with the submission

The submission record SHALL carry the findings the client determined, and SHALL
keep the inventory document whole alongside them.

#### Scenario: Findings written into the record
- **WHEN** a submission carries an asset inventory
- **THEN** `submission.json` holds its findings, beside the asset ID, owner and
  class already recorded there

#### Scenario: The whole document is kept
- **WHEN** an inventory is stored
- **THEN** the complete document is kept, so fields the server does not model
  today are not discarded

#### Scenario: Unknown schema version
- **WHEN** an inventory declares a `schema_version` the server does not
  recognise
- **THEN** the document is stored and the fields the server understands are
  used; the submission is not refused

#### Scenario: Malformed inventory
- **WHEN** an inventory cannot be parsed
- **THEN** it is logged and skipped, and the submission is stored as it
  otherwise would be

#### Scenario: No inventory present
- **WHEN** a submission carries no inventory
- **THEN** the record holds none, and the submission is otherwise unaffected
