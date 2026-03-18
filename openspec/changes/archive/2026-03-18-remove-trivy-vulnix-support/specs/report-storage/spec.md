## MODIFIED Requirements

### Requirement: File Naming

Each report type SHALL map to a specific filename in the host directory.

| Report Type | Filename |
|-------------|----------|
| lynis | `lynis-report.json` |
| neofetch | `neofetch-report.json` |

#### Scenario: Lynis report storage
- **WHEN** server receives a valid lynis report
- **THEN** server stores it as `lynis-report.json` in the appropriate host directory

#### Scenario: Neofetch report storage
- **WHEN** server receives a valid neofetch report
- **THEN** server stores it as `neofetch-report.json` in the appropriate host directory

## REMOVED Requirements

### Requirement: Trivy report filename mapping
**Reason**: Trivy report type is no longer supported
**Migration**: Existing `trivy-report.json` files will remain on disk but will not be processed or displayed. Remove client-side Trivy scan submissions.

### Requirement: Vulnix report filename mapping
**Reason**: Vulnix report type is no longer supported
**Migration**: Existing `vulnix-report.json` files will remain on disk but will not be processed or displayed. Remove client-side Vulnix scan submissions.
