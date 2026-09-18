## ADDED Requirements

### Requirement: A note may sit beside a row

The register format SHALL accept comment lines, so that a decision about a row
can be recorded next to it. A line whose first non-whitespace character is `#`
SHALL be ignored when the register is read, wherever in the file it appears. The
service SHALL NOT read meaning out of a comment, and SHALL NOT be required to
preserve one.

#### Scenario: A note above the header
- **WHEN** the register opens with one or more `#` lines before its header line
- **THEN** the header is the first line that is not a note, and the register
  loads

#### Scenario: A note between rows
- **WHEN** a `#` line sits between two asset rows
- **THEN** it is skipped, both rows load, and the note is not parsed as a row

#### Scenario: A note is indented under its row
- **WHEN** a note is written with leading whitespace before the `#`
- **THEN** it is a note, because a register value never begins with whitespace
  either

#### Scenario: Errors still name the line in the file
- **WHEN** a row fails validation in a register that holds notes
- **THEN** the error names the line number the line has in the file, counting
  the notes, so that the number leads to the line the maintainer opens

#### Scenario: Nothing is parsed out of a note
- **WHEN** a note is written in the shape of an instruction, such as an
  exception for an asset or a field the loader knows
- **THEN** it has no effect; a fact the service acts on belongs in a column,
  where it is validated

#### Scenario: A register of only notes
- **WHEN** every line in the register is a note
- **THEN** it is an empty register and the service refuses to start, with an
  error saying the file has no header line

## MODIFIED Requirements

### Requirement: Load asset register

The system SHALL load an asset register from a CSV file exported from the ISO
reporting sheet, mapping hardware serial to asset ID, owner and platform class.
Where the register's header line cannot be used, the error SHALL name and quote
the line that was read as the header, as well as the columns that were expected.

#### Scenario: Register loaded at startup
- **WHEN** `compliance.asset_register` points to a readable CSV with columns
  `asset_id, serial, owner, model, class, status`
- **THEN** the system loads all entries and logs the count

#### Scenario: Duplicate serial
- **WHEN** the register contains the same serial twice
- **THEN** the system fails to start with an error naming the serial and both
  asset IDs

#### Scenario: Unknown platform class
- **WHEN** a register row has a class outside `linux`, `macos`, `windows`
- **THEN** the system fails to start with an error naming the row

#### Scenario: Register absent
- **WHEN** no asset register is configured
- **THEN** the system starts, accepts submissions, and reports that the round
  and fleet views are unavailable

#### Scenario: The header line cannot be used
- **WHEN** the line read as the header does not carry the required columns -
  because the file opens with a data row, or was exported with another separator
- **THEN** the service refuses to start with an error giving that line's number
  and its text as read, so that the reader is sent to the line at fault rather
  than to columns that are present
