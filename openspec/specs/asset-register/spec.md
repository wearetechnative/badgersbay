# asset-register Specification

## Purpose
Defines the asset register: the list of systems in ISO scope, exported from the compliance sheet, against which coverage is measured. The register is the denominator - without it the server can show what arrived but never which systems are missing. asset_id is the durable identity and the hardware serial is the key an incoming submission is matched on.

## Requirements

### Requirement: Load asset register

The system SHALL load an asset register from a CSV file exported from the ISO
reporting sheet, mapping hardware serial to asset ID, owner and platform class.

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
