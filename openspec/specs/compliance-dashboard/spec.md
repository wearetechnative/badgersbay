# Compliance Dashboard

## Purpose
Defines what the compliance dashboard shows per system: the operating system
reported by the client, and links to the stored evidence for that system.

## Requirements

### Requirement: Display OS type information

The system SHALL display OS type for each system, read from the stored
fastfetch report, updating immediately upon report upload.

#### Scenario: OS type from neofetch data
- **WHEN** a system directory contains `neofetch-report.json` from an earlier
  client generation and no `fastfetch-report.json`
- **THEN** the dashboard displays "unknown" and does not read the legacy file
  as system information

#### Scenario: OS type from fastfetch data
- **WHEN** a client uploads fastfetch data with `{"os": "NixOS 26.05 (Yarara)"}`
- **THEN** the dashboard displays "NixOS 26.05 (Yarara)" in the OS Type column

#### Scenario: OS type updates without server restart
- **WHEN** a client uploads a new fastfetch report with a different OS version
- **THEN** a dashboard refresh shows the updated OS type

#### Scenario: OS type from tar submission header
- **WHEN** a client submits a tar archive that carries no fastfetch member but
  does send an `X-OS-Type` header
- **THEN** the dashboard displays that value; the header is now a fallback,
  because an archive containing fastfetch data is read directly

#### Scenario: Unknown OS type
- **WHEN** a system has no fastfetch report, or one without an `os` field
- **THEN** the dashboard displays "unknown" for OS type

#### Scenario: Dashboard refresh retrieves latest OS type
- **WHEN** a user clicks refresh or auto-refresh triggers
- **THEN** the dashboard shows the current OS type from the cache without
  requiring a server restart


### Requirement: Display tar archive download links

The system SHALL provide download links for tar archives with recognizable filenames.

#### Scenario: Tar badge links to most recent tar
- **WHEN** system has uploaded tar archive(s)
- **THEN** dashboard TAR badge links to most recently uploaded tar file

#### Scenario: Downloaded tar has meaningful filename
- **WHEN** user clicks TAR badge for system "lobos-wtoorren" with file `honeybadger-20260330-142931.tar.gz`
- **THEN** browser downloads as `lobos-wtoorren-honeybadger-20260330-142931.tar.gz`

#### Scenario: Tar badge handles both naming conventions
- **WHEN** system directory contains both `submission-*` and `honeybadger-*` tar files
- **THEN** dashboard links to most recent by modification time

### Requirement: Dashboard view organized by audit period

The system SHALL display the dashboard organized by audit period when compliance mode is enabled, replacing the chronological date-based view.

#### Scenario: Compliance mode dashboard structure
- **WHEN** compliance.enabled is true and user accesses dashboard
- **THEN** dashboard shows audit period selector and period-based compliance view

#### Scenario: Legacy mode dashboard structure
- **WHEN** compliance.enabled is false or not configured
- **THEN** dashboard shows traditional chronological listing by upload date

#### Scenario: Period selection
- **WHEN** user selects audit period "2026-03" from dropdown
- **THEN** dashboard displays all systems with uploads in that period

### Requirement: Display compliance summary statistics

The system SHALL display summary statistics for the selected audit period at the top of the dashboard.

#### Scenario: Summary statistics displayed
- **WHEN** viewing audit period dashboard
- **THEN** displays: total systems, complete count, incomplete count, compliance percentage

#### Scenario: Example summary
- **WHEN** period has 42 systems total, 38 complete, 4 incomplete
- **THEN** shows "Total: 42 | Complete: 38 (90%) | Incomplete: 4 (10%)"

### Requirement: Display system compliance table in compliance mode

The system SHALL display a table showing compliance status for each system in the audit period using hostname instead of SID.

**Columns:**
- Hostname (from X-Hostname header)
- Username
- OS Type
- Upload Date (latest upload in period)
- Reports (badges: F L)
- Status (Complete/Incomplete with details)

#### Scenario: Complete system row in compliance mode
- **WHEN** webserver01 has a complete set in 2026-09
- **THEN** row shows: "webserver01 | admin | ubuntu | 2026-09-15 | F L | ✓ Complete"

#### Scenario: Incomplete system row in compliance mode
- **WHEN** dbserver02 is missing lynis in 2026-09
- **THEN** row shows: "dbserver02 | dbadmin | nixos | 2026-09-10 | F | ⚠ Missing: lynis"

#### Scenario: No SID column
- **WHEN** viewing the compliance dashboard table
- **THEN** the table does NOT include a SID column; Hostname is the first column

### Requirement: Period navigation

The system SHALL allow users to navigate between different audit periods.

#### Scenario: Period dropdown
- **WHEN** user clicks period selector
- **THEN** dropdown shows all available audit periods in reverse chronological order

#### Scenario: Switch period
- **WHEN** user selects different period from dropdown
- **THEN** dashboard refreshes to show data for selected period

### Requirement: Filter by compliance status

The system SHALL allow filtering systems by compliance status.

#### Scenario: Show all systems
- **WHEN** filter set to "All"
- **THEN** all systems in period are displayed

#### Scenario: Show only incomplete
- **WHEN** filter set to "Incomplete"
- **THEN** only systems with incomplete or missing reports are shown

#### Scenario: Show only complete
- **WHEN** filter set to "Complete"
- **THEN** only systems with complete report sets are shown

### Requirement: Report badge for fastfetch

The system SHALL render the system information report as badge `F` linking to
the stored `fastfetch-report.json`.

#### Scenario: Badge rendered for present report
- **WHEN** a system has `fastfetch-report.json` in the selected audit period
- **THEN** the Reports column shows badge `F` linking to that file

#### Scenario: Legend reflects current report types
- **WHEN** the dashboard renders its legend
- **THEN** it reads "F=Fastfetch, L=Lynis, TAR=Tar Archive"

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

### Requirement: Show the audit's findings in the fleet view

The fleet view SHALL show the compliance values the client determined, so they
can be read off rather than reconstructed by hand.

#### Scenario: Findings shown
- **WHEN** an asset's latest submission carries an inventory
- **THEN** the row shows disk encryption, screen lock, firewall, hardening
  score, OS up-to-date and vulnerable packages

#### Scenario: A measurement without a verdict
- **WHEN** a finding carries a null value and a count, as the client emits for
  vulnerable packages because the register contradicts itself about which
  literal means compliant
- **THEN** the cell shows the count and the client's reason, and is treated as
  known

#### Scenario: A declined value reads as unknown with its reason
- **WHEN** a finding carries a null value, no count and a populated finding text
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

### Requirement: Reach an earlier round from the dashboard

The dashboard SHALL offer a control for selecting which scan round is shown, so
that a closed round can be read without knowing the URL scheme.

#### Scenario: The control is on every view
- **WHEN** either the scan round view or the fleet view is rendered
- **THEN** the round selector is present and marks the round being shown

#### Scenario: Changing the round keeps the view
- **WHEN** a reader on the fleet view selects a different round
- **THEN** the fleet view for that round is shown, not the other view

#### Scenario: Which rounds are offered
- **WHEN** the selector is rendered
- **THEN** it offers the rounds that have submissions together with the current
  round, newest first, so the round being viewed never disappears from its own
  selector while it is still empty

#### Scenario: Selection survives being shared
- **WHEN** a selected round is reached
- **THEN** the address carries the round, so reloading or sending the address to
  someone else shows the same round

#### Scenario: A round nobody submitted to
- **WHEN** a round with no submissions is selected
- **THEN** it renders as a round in which nothing was scanned, with the register
  still naming who was expected, rather than as an error

#### Scenario: A closed round keeps its own denominator
- **WHEN** a past round is shown
- **THEN** the assets counted are those whose validity window overlapped that
  round, not those in the register today, so a historical figure does not change
  when the register does
