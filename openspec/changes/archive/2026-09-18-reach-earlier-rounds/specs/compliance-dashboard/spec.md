## ADDED Requirements

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
