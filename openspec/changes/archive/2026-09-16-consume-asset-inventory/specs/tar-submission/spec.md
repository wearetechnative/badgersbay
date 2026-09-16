## MODIFIED Requirements

### Requirement: Extract recognised reports from the archive

The server SHALL extract JSON members whose report type it recognises and SHALL
store each through the normal report storage path, alongside the archive. It
SHALL also extract the asset inventory, which is a summary of those reports
rather than a report itself.

#### Scenario: Reports extracted and stored
- **WHEN** an archive contains `fastfetch.json` and `lynis-report.json`
- **THEN** both are stored as `fastfetch-report.json` and `lynis-report.json`
  in the same directory as the archive

#### Scenario: Asset inventory extracted
- **WHEN** an archive contains `asset-inventory.json`
- **THEN** it is stored in the submission record and is not reported as an
  unrecognised member

#### Scenario: The inventory is not a report type
- **WHEN** an archive carries an asset inventory
- **THEN** it does not contribute to completeness, and its absence is not a
  missing requirement

#### Scenario: Completeness reflects contents
- **WHEN** an archive containing a complete report set is submitted
- **THEN** the system is recorded complete, rather than recorded as holding
  only an archive

#### Scenario: Non-JSON members ignored
- **WHEN** an archive contains `hardware-serial.txt`, `asset-inventory.txt` or
  other non-JSON members
- **THEN** they are left in the stored archive and not extracted

#### Scenario: Previously stored archives unaffected
- **WHEN** archives stored before this behaviour existed are present on disk
- **THEN** they are not re-processed, and the periods holding them keep their
  recorded figures
