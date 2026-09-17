## ADDED Requirements

### Requirement: Evidence route serves the trees the server writes

The system SHALL serve a file from any submission record it has written,
whether or not that record resolved to a register entry, and SHALL name the
tree in the path rather than inferring it from the key.

#### Scenario: Unmatched submission is downloadable
- **WHEN** a user requests
  `/evidence/unmatched/lobos-wtoorren/2026-09-17T09-00-00/lynis-report.json`
- **THEN** the file stored under
  `reports/unmatched/lobos-wtoorren/2026-09-17T09-00-00/` is served, named by
  the convention for a submission with no asset

#### Scenario: Existing links keep working
- **WHEN** a path names three segments, as every link emitted before the
  unmatched tree was served did
- **THEN** it is read as a record under the serial-keyed tree and served
  unchanged

#### Scenario: The period archive is not served through this route
- **WHEN** a path names `2026-03` as its tree
- **THEN** the request is refused, because the archive is history the server
  only reads and its records are reached through the legacy report route

#### Scenario: A path that climbs is refused
- **WHEN** any segment of the path is empty, `.`, `..`, or contains a separator
- **THEN** the request is refused before any file is opened

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
