## MODIFIED Requirements

### Requirement: Configure required reports

The system SHALL define required reports by requirement name and platform
class, not by tool name.

#### Scenario: Configure mandatory reports
- **WHEN** config.yaml configures the mandatory requirements for a platform
  class
- **THEN** those requirements are required for every asset of that class

#### Scenario: Configure one-of scanner requirement
- **WHEN** a platform class configures a non-empty `one_of` list
- **THEN** at least one of the listed requirements must be satisfied

#### Scenario: Default configuration
- **WHEN** no per-class configuration is given
- **THEN** the system defaults to `sysinfo` and `hardening` as mandatory for
  every class

#### Scenario: Linux and macOS requirements
- **WHEN** a register entry has class `linux` or `macos`
- **THEN** a complete submission requires `sysinfo` (fastfetch.json) and
  `hardening` (lynis-report.json)

#### Scenario: Windows requirements
- **WHEN** a register entry has class `windows`
- **THEN** a complete submission requires `sysinfo` and `hardening`
  (hardeningkitty.csv)

#### Scenario: Class comes from the register
- **WHEN** determining which reports a submission must contain
- **THEN** the platform class is read from the asset register, not inferred
  from the submission contents

#### Scenario: Windows before client support exists
- **WHEN** a register entry has class `windows` and the client cannot yet
  submit
- **THEN** the asset is reported as `manual` rather than incomplete

#### Scenario: Missing system information report
- **WHEN** a submission satisfies `hardening` but carries nothing that
  satisfies `sysinfo`
- **THEN** the report set is incomplete with reason "Missing sysinfo"

#### Scenario: Complete set
- **WHEN** a submission satisfies every mandatory requirement for its platform
  class
- **THEN** the report set is marked complete
