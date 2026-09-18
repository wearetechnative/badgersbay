# asset-register Specification

## Purpose
Defines the asset register: the list of systems in ISO scope, exported from the compliance sheet, against which coverage is measured. The register is the denominator - without it the server can show what arrived but never which systems are missing. asset_id is the durable identity and the hardware serial is the key an incoming submission is matched on.

## Requirements

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

### Requirement: Resolve submission to register entry

The system SHALL identify a submission by the hardware serial contained in its
tar archive and resolve it against the asset register.

#### Scenario: Serial matches a register entry
- **WHEN** a tar contains `hardware-serial.txt` with `PF50L2MR` and the register
  holds that serial for TARI-00023
- **THEN** the submission is recorded against TARI-00023

#### Scenario: Serial normalisation
- **WHEN** the serial file contains leading whitespace, a trailing newline, a
  byte order mark, or lowercase characters
- **THEN** the value is normalised before lookup and still matches

#### Scenario: Serial not in register
- **WHEN** a submission carries serial `YD063JGA` which is absent from the
  register
- **THEN** the submission is stored under `reports/unmatched/` and surfaced on
  the dashboard as an unmatched submission

#### Scenario: Serial unreadable
- **WHEN** a tar contains no `hardware-serial.txt` or the file is empty
- **THEN** the submission is stored as unmatched with reason `no_serial` and is
  never rejected

#### Scenario: Placeholder serial
- **WHEN** the serial file holds a known placeholder such as `Not available`,
  `Not available (VM or unknown hardware)`, `To Be Filled`, `Default string` or
  all zeroes
- **THEN** it is treated as absent, not as a lookup key

#### Scenario: Malformed serial
- **WHEN** the serial value contains whitespace, as the macOS client's
  `Mac OS X` output does
- **THEN** it is treated as absent rather than used as a key

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

### Requirement: Asset identity and serial lookup

The system SHALL treat `asset_id` as the durable identity of an asset and the
hardware serial as the key by which a submission is matched to it. An asset MAY
have more than one serial over its lifetime.

#### Scenario: Several serials for one asset
- **WHEN** TARI-00023 has rows for serials `PF50L2MR` (valid until 2026-06-01)
  and `PG81N4QX` (valid from 2026-06-01)
- **THEN** submissions carrying either serial resolve to TARI-00023 and form one
  continuous history

#### Scenario: Overlapping validity rejected
- **WHEN** two rows for one serial have overlapping validity windows
- **THEN** the system fails to start with an error naming the serial

### Requirement: Retired assets

The system SHALL exclude assets with status `retired` from the round
denominator while retaining them and their history.

#### Scenario: Retired asset excluded from the count
- **WHEN** the register holds eleven assets of which one is retired
- **THEN** the round denominator is ten and the retired asset is listed
  separately

#### Scenario: Retired asset keeps its history
- **WHEN** a retired asset submitted in an earlier round
- **THEN** those submissions remain readable and remain counted in that earlier
  round

#### Scenario: Missing row is not retirement
- **WHEN** an asset present in the previous register is absent from a newly
  loaded one
- **THEN** the system reports the disappearance rather than treating it as a
  retirement

### Requirement: Scope membership by validity window

The system SHALL determine which assets belong to an audit round from the
validity window recorded in the register, not from a snapshot taken when the
round opened.

#### Scenario: Asset in scope for the whole round
- **WHEN** an asset's validity window spans the 2026-09 scan window
- **THEN** it is counted in that round's denominator

#### Scenario: Replacement issued mid-round
- **WHEN** a device is written off on 2026-09-20 and a replacement enters the
  register on 2026-09-22, inside the scan window
- **THEN** the replacement is in scope for the 2026-09 round and appears as
  outstanding until it submits

#### Scenario: New employee mid-round
- **WHEN** an asset enters the register during the scan window of the open round
- **THEN** it is in scope for that round

#### Scenario: Asset entering after the scan window closes
- **WHEN** an asset enters the register after the scan window and grace period
  of the open round have passed
- **THEN** it is out of scope for that round, in scope for the next, and shown
  in the fleet view immediately as never audited

#### Scenario: Historical round is reproducible
- **WHEN** the 2026-03 round is recomputed after the register has changed
- **THEN** its denominator is unchanged, because membership derives from
  recorded validity dates

### Requirement: Leaving scope during a round

The system SHALL record an asset's departure from scope with a reason and SHALL
NOT silently remove it from a round it was part of.

#### Scenario: Device stolen mid-round before being scanned
- **WHEN** an asset leaves scope on 2026-09-20 with a reason and has no
  submission in that round
- **THEN** it is reported as accounted for, with the reason, and is not counted
  as scanned

#### Scenario: Departure without a reason
- **WHEN** an asset's validity window is closed without a reason
- **THEN** the system reports it as an unexplained departure rather than
  removing it from the denominator

#### Scenario: Departure after being scanned
- **WHEN** an asset submits and then leaves scope within the same round
- **THEN** the submission still counts for that round

### Requirement: Record register state on each submission

The system SHALL write the asset ID, owner and platform class into a submission
record at storage time.

#### Scenario: Ownership recorded as it was
- **WHEN** TARI-00002 submits while owned by Pim Snel and later transfers
- **THEN** the earlier submission still reports Pim Snel as owner

#### Scenario: Round view chases the current owner
- **WHEN** an asset has transferred since its last submission
- **THEN** the round view lists it under its current owner while the historical
  record keeps the former one

#### Scenario: Evidence predating the current holder
- **WHEN** a submission's scan date precedes the asset's `owner_since`
- **THEN** the system flags it as evidence predating the current holder

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
