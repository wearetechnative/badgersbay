## ADDED Requirements

### Requirement: Narrow the scan round view

The scan round view SHALL offer filtering of its per-asset table by state, by
owner and by platform class, and SHALL allow one asset to be found by its
identifier or its hardware serial.

#### Scenario: Narrow by state
- **WHEN** the outstanding state is selected
- **THEN** the table shows the outstanding assets and no others

#### Scenario: Accounted for is one state
- **WHEN** the accounted-for state is selected
- **THEN** both the assets resolved by a recorded exception and the assets that
  left scope with a reason are shown, because they read as one section

#### Scenario: Narrow by owner
- **WHEN** an owner is selected
- **THEN** the table shows that owner's assets, matched on the name as the
  register holds it rather than on the proof-file slug, which is lossy and can
  be shared by two owners

#### Scenario: Narrow by platform class
- **WHEN** a platform class is selected
- **THEN** the table shows the assets of that class, so the part of the fleet
  whose client can submit can be read on its own

#### Scenario: Terms compose
- **WHEN** an owner and a state are both given
- **THEN** the table shows the assets matching both

#### Scenario: Find an asset by identifier
- **WHEN** a search reads `TARI-00031`, `00031` or `31`
- **THEN** the row for TARI-00031 is shown

#### Scenario: Find an asset by serial however it is spelled
- **WHEN** a serial is searched for with the separators the ISO tool writes, or
  without them as the machine reports it
- **THEN** the same asset is found either way

#### Scenario: A term that matches nothing
- **WHEN** a filter matches no asset in the round
- **THEN** the table is empty and the view says the filter is why, rather than
  leaving it to read as a round with nothing in it

#### Scenario: An unrecognised state
- **WHEN** the address carries a state that is not one of the view's states
- **THEN** it is not honoured, the whole round is shown, and the view says the
  value was not understood

### Requirement: A filter never changes the round's figures

The scan round view SHALL compute its progress figures from the unfiltered
round, however the table is narrowed, because those figures are statements
about the round rather than about the reader's view.

#### Scenario: The headline is about the round
- **WHEN** the table is narrowed to the outstanding assets of one owner
- **THEN** the count of assets scanned and the round's denominator are the same
  as with no filter

#### Scenario: The meter and the bucket counts hold
- **WHEN** any filter is active
- **THEN** the scanned, accounted-for and outstanding counts beside the meter
  are those of the whole round

#### Scenario: The per-owner bars hold
- **WHEN** the table is narrowed to one owner
- **THEN** every owner is still listed in the progress panel with their own
  count, so the panel keeps describing the round

### Requirement: A filter is shareable

A filtered scan round view SHALL be addressable, so that it survives a reload
and can be sent to the person it concerns.

#### Scenario: The address carries the filter
- **WHEN** a filter is applied
- **THEN** the address carries it, and fetching that address again shows the
  same narrowed view

#### Scenario: The filter composes with the round
- **WHEN** a filtered view of a closed round is addressed
- **THEN** that round is shown, narrowed by that filter

#### Scenario: Changing the round keeps the filter
- **WHEN** a reader with a filter active selects a different round
- **THEN** the filter is still applied to the round they arrive at

#### Scenario: The control needs no scripting
- **WHEN** the filter is applied
- **THEN** it is applied by submitting a form to the server, not by a script
  rewriting the page

### Requirement: Say when a filter is hiding something

The scan round view SHALL state, whenever a filter is active, which terms are
active and how many of the round's assets they hide, and SHALL offer a way back
to the whole round.

#### Scenario: The notice names the filter
- **WHEN** a filter is active
- **THEN** the view names the active terms and the number of assets shown of
  the number in the round

#### Scenario: A filter that hides nothing is still announced
- **WHEN** a filter matches every asset in the round
- **THEN** the notice is still shown, so a shared address is not read as the
  full picture

#### Scenario: The way back
- **WHEN** a filter is active
- **THEN** the view offers a link to the same round with no filter

### Requirement: The per-owner bars reach that owner's assets

The progress panel's per-owner bars SHALL link to the round view narrowed to
that owner, and SHALL mark the owner currently being shown.

#### Scenario: A bar is a link
- **WHEN** the progress panel is rendered
- **THEN** each owner's bar links to the round view filtered to that owner

#### Scenario: The active owner is marked
- **WHEN** the view is narrowed to one owner
- **THEN** that owner's bar is marked as the one being shown
