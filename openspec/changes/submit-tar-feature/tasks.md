# Implementation Tasks

## 1. Add Trivy and Vulnix Report Type Support

- [x] 1.1 Update `valid_types` list to include 'trivy' and 'vulnix' in `validate_report_type()` function
- [x] 1.2 Add Trivy validation logic in `validate_report_structure()` checking for 'Results' or 'ArtifactName' fields
- [x] 1.3 Add Vulnix validation logic in `validate_report_structure()` checking for 'vulnerabilities' field
- [x] 1.4 Add filename mappings for Trivy and Vulnix in `save_report()` function

## 2. Implement Tar Archive Handling Infrastructure

- [x] 2.1 Add `import tarfile` and `import io` at top of honeybadger_server.py
- [x] 2.2 Create helper function `detect_report_type_from_filename(filename)` that matches patterns (lynis.json, neofetch-report.json, etc.)
- [x] 2.3 Create helper function `validate_tar_member_path(member)` that checks for absolute paths, '..' traversal, and symlinks
- [x] 2.4 Create helper function `validate_tar_size_limits(content_length, member_sizes)` checking 50MB total and 10MB per file

## 3. Implement Tar Extraction and Validation

- [x] 3.1 Create function `extract_and_validate_tar(tar_data)` that opens tar with `tarfile.open(fileobj=io.BytesIO(tar_data), mode='r:*')`
- [x] 3.2 Add pre-scan loop in extract function to validate all members before extraction (paths, sizes, file count < 100)
- [x] 3.3 Add extraction loop that processes JSON files, detects types from filenames, and collects content
- [x] 3.4 Return list of tuples: [(filename, report_type, json_content), ...]

## 4. Implement /submit-tar Endpoint Handler

- [x] 4.1 Add `do_POST_submit_tar()` method to ReportHandler class
- [x] 4.2 Extract X-Hostname and X-Username headers (required, fail with 400 if missing)
- [x] 4.3 Check Content-Length header against 50MB limit, return 413 if exceeded
- [x] 4.4 Read request body and call `extract_and_validate_tar()`, handle exceptions with 400 response
- [x] 4.5 Loop through extracted reports, validate each using existing `validate_report_structure()` function
- [x] 4.6 Save each valid report using existing `save_report()` function, collect results
- [x] 4.7 Build response JSON with per-file status (saved/error) and overall message
- [x] 4.8 Return HTTP 200 if all succeeded, 207 if partial, 400 if all failed

## 5. Update Request Routing

- [x] 5.1 Modify `do_POST()` method to check if path is '/submit-tar' and call `do_POST_submit_tar()` accordingly
- [x] 5.2 Ensure existing POST '/' behavior remains unchanged for backwards compatibility

## 6. Testing and Validation

- [x] 6.1 Create test script `test-tar-submit.sh` that generates sample tar with lynis, neofetch, trivy, and vulnix reports
- [x] 6.2 Test successful submission of valid tar archive with all 4 report types
- [x] 6.3 Test path traversal protection (tar with '../etc/passwd')
- [x] 6.4 Test absolute path rejection (tar with '/tmp/report.json')
- [x] 6.5 Test size limit enforcement (tar > 50MB and individual file > 10MB)
- [x] 6.6 Test partial failure scenario (tar with 2 valid + 1 invalid report)
- [x] 6.7 Test corrupted tar archive handling
- [x] 6.8 Test gzip-compressed tar (.tar.gz) support
- [x] 6.9 Verify dashboard displays all 4 report types correctly
- [x] 6.10 Test backwards compatibility with existing single-report POST endpoint

## 7. Documentation

- [x] 7.1 Add /submit-tar endpoint documentation to README.md with curl examples
- [x] 7.2 Document filename patterns for report type detection in README.md
- [x] 7.3 Update CLAUDE.md to reflect new endpoint and supported report types
- [x] 7.4 Document size limits (50MB tar, 10MB per file) in README.md
- [x] 7.5 Add example client script showing tar creation and submission
