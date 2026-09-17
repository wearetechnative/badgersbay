## MODIFIED Requirements

### Requirement: Download filename follows the register convention

The system SHALL serve every file belonging to a submission under the proof file
naming convention used by the ISO reporting sheet, so that a download can be
filed as evidence without being renamed.

#### Scenario: Matched asset download
- **WHEN** a user downloads the tar for TARI-00023, owner Wouter van der
  Toorren, submitted 2026-09-15
- **THEN** the browser receives it as
  `TARI-00023-2026-09-15-wouter.toorren.tar.gz`

#### Scenario: Reports carry the same convention
- **WHEN** a user downloads a report belonging to that submission
- **THEN** the name follows the same convention with the report type appended,
  as `TARI-00023-2026-09-15-wouter.toorren-lynis.json`

#### Scenario: Two assets do not collide
- **WHEN** reports for two different assets are downloaded into one folder
- **THEN** neither overwrites the other, because the asset and the round are in
  the name rather than only the report type

#### Scenario: A submission with no asset
- **WHEN** a file belonging to a submission that matched no asset is named
- **THEN** the name carries the identity that submission does have - its
  hardware serial, or the hostname and username it arrived under - with its
  date, rather than the name the file had inside the archive

**Note:** the evidence route resolves only under the serial-keyed tree, so an
unmatched submission cannot be downloaded through it today. The rule above is
what applies once it can; the missing route is tracked separately.
