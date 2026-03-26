## Why

Currently, clients must submit each report type (Lynis, Trivy, Vulnix, Neofetch) as separate HTTP POST requests to the honeybadger server. This creates unnecessary network overhead and complexity in client scripts, especially when scanning systems behind unreliable networks or when submitting multiple reports. A single tar archive submission would simplify client-side logic and reduce network round-trips.

## What Changes

- Add new endpoint `/submit-tar` that accepts a tar archive containing multiple report JSON files
- Validate tar contents before extraction (file types, structure, malicious paths)
- Extract reports from tar and process them using existing validation and storage logic
- Maintain backwards compatibility with existing single-report POST endpoints
- Add error handling for corrupted or malicious tar files

## Capabilities

### New Capabilities
- `tar-submission`: Accept and process tar archives containing multiple security scan reports in a single HTTP request

### Modified Capabilities
- `report-ingestion`: Update to support both individual JSON submissions and tar archive submissions

## Impact

- **Code**: Adds new POST handler for `/submit-tar` endpoint in `honeybadger_server.py`
- **Validation**: Extends existing validation logic to handle tar extraction and multi-report processing
- **Storage**: Reuses existing storage functions, no changes to filesystem layout
- **Clients**: Optional feature - existing single-report clients continue to work unchanged
- **Dependencies**: May require adding `tarfile` module (Python stdlib, already available)
