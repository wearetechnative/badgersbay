# Tar Submission Feature - Design

## Context

Currently, the honeybadger server accepts individual security scan reports via HTTP POST to the root endpoint (`/`). Clients must make separate POST requests for each report type (Lynis, Neofetch, Trivy, Vulnix). This design adds a new endpoint `/submit-tar` that accepts a tar archive containing multiple reports, reducing network overhead and simplifying client-side scripting.

The existing architecture is a single-file Python HTTP server with filesystem-based storage. All reports are stored in directories named `<hostname>-<username>-<yyyymmdd>/`. The server uses Python's standard library exclusively (except PyYAML for config).

## Goals / Non-Goals

**Goals:**
- Accept tar archives containing multiple JSON report files via new `/submit-tar` endpoint
- Detect report types automatically from filenames within the tar
- Reuse existing validation and storage functions for each report
- Maintain single-file architecture and stdlib-only dependencies (tarfile is stdlib)
- Provide detailed per-file success/failure responses
- Protect against path traversal and archive bomb attacks

**Non-Goals:**
- Replace the existing single-report POST endpoint (backwards compatibility required)
- Support non-JSON files in the tar archive
- Add report preprocessing or transformation
- Implement streaming tar extraction (use in-memory extraction for simplicity)
- Support zip or other archive formats (tar/tar.gz only)

## Decisions

### Decision 1: Add new `/submit-tar` endpoint instead of modifying existing `/` endpoint

**Rationale:** Keeps backwards compatibility clean. Existing clients continue using POST to `/` with headers. New clients use POST to `/submit-tar` with tar payload.

**Alternatives considered:**
- Overload POST `/` to auto-detect tar vs JSON: Increases complexity and error-prone (what if tar contains valid JSON-like bytes?)
- Use query parameter like `POST /?format=tar`: Less RESTful, harder to document

**Decision:** Separate endpoint. Clean separation of concerns.

### Decision 2: Detect report type from filename patterns

**Rationale:** Avoids requiring X-Report-Type header for each file in the archive. Client can simply include files named `lynis-report.json`, `neofetch.json`, etc.

**Patterns:**
- `lynis-report.json`, `lynis.json` → type `lynis`
- `neofetch-report.json`, `neofetch.json` → type `neofetch`
- `trivy-report.json`, `trivy.json` → type `trivy`
- `vulnix-report.json`, `vulnix.json` → type `vulnix`

**Alternatives considered:**
- Require manifest file in tar (e.g., `manifest.json` listing each file and type): Adds complexity for clients, one more thing to go wrong
- Use directory structure in tar (e.g., `lynis/report.json`): More flexible but harder to validate and document

**Decision:** Filename pattern matching. Simple for clients, easy to implement.

### Decision 3: Extract tar to memory, not disk

**Rationale:** Keeps server stateless and avoids cleanup logic. Tar archives are expected to be small (< 50MB total, < 10MB per file).

**Implementation:**
```python
import tarfile
import io

tar = tarfile.open(fileobj=io.BytesIO(request_body), mode='r:*')
for member in tar.getmembers():
    if member.isfile() and member.name.endswith('.json'):
        content = tar.extractfile(member).read()
        # Process content
```

**Alternatives considered:**
- Extract to temporary directory: Requires cleanup on failure, potential disk space issues
- Stream processing: More complex, not needed for small archives

**Decision:** In-memory extraction using `io.BytesIO`.

### Decision 4: Validate paths before extraction

**Rationale:** Prevent path traversal attacks (e.g., `../../etc/passwd`) and absolute paths.

**Validation checks:**
- Reject absolute paths: `member.name.startswith('/')`
- Reject parent directory traversal: `'..' in member.name`
- Reject symlinks: `member.issym() or member.islnk()`

**Fail-fast:** If any member violates these rules, reject entire archive with HTTP 400.

**Decision:** Pre-scan all tar members before processing any. One bad file fails entire submission.

### Decision 5: Return HTTP 207 Multi-Status for partial failures

**Rationale:** If tar contains 3 files and 2 succeed but 1 fails validation, the client should know which succeeded and which failed.

**Response format:**
```json
{
  "status": "partial",
  "message": "Processed 2/3 reports, 1 failed",
  "results": [
    {"file": "lynis.json", "type": "lynis", "status": "saved", "path": "..."},
    {"file": "neofetch.json", "type": "neofetch", "status": "error", "error": "..."},
    {"file": "trivy.json", "type": "trivy", "status": "saved", "path": "..."}
  ]
}
```

**Alternatives considered:**
- All-or-nothing: Reject entire tar if any file fails: Too strict, wastes successful validations
- HTTP 200 even with failures: Misleading, client might not check details

**Decision:** HTTP 207 for partial success, HTTP 200 for full success, HTTP 400 if all fail or archive invalid.

### Decision 6: Support both `.tar` and `.tar.gz` transparently

**Rationale:** Compression reduces bandwidth. Python's `tarfile.open(mode='r:*')` auto-detects compression.

**Implementation:** Detect from content (gzip magic bytes) rather than Content-Type header.

**Decision:** Support both automatically using `mode='r:*'` (auto-detection mode).

### Decision 7: Enforce size limits

**Rationale:** Prevent memory exhaustion from large archives.

**Limits:**
- Total tar archive: 50MB
- Individual JSON file: 10MB

**Implementation:** Check `Content-Length` header for total size, check `member.size` before extraction.

**Decision:** Fail-fast with HTTP 413 (Payload Too Large) if limits exceeded.

## Risks / Trade-offs

### Risk: In-memory extraction with large archives → Memory exhaustion
**Mitigation:** Enforce 50MB archive limit and 10MB per-file limit. Reject before extraction starts.

### Risk: Malicious tar bombs (deeply nested directories, many small files)
**Mitigation:** Limit extraction to 100 files maximum, reject nested paths with depth > 3. Pre-scan all members before extracting any.

### Risk: Filename collision (two files map to same report type)
**Mitigation:** Last file wins (overwrites). Document this behavior. Consider rejecting with error in future if needed.

### Trade-off: HTTP 207 Multi-Status not universally supported by clients
**Impact:** Some HTTP clients may not handle 207 properly. Mitigation: Include clear "status" field in JSON so clients can parse response body regardless of status code.

### Trade-off: Filename-based type detection limits flexibility
**Impact:** Clients must follow naming conventions. Mitigation: Document clearly in README with examples. Alternatively, could add optional manifest file in future.

## Migration Plan

### Deployment Steps

1. **Add new handler to `honeybadger_server.py`**
   - Add `do_POST_submit_tar()` method to `ReportHandler` class
   - Route `/submit-tar` requests to new handler
   - Reuse existing `validate_report_structure()` and `save_report()` functions

2. **Add Trivy/Vulnix validation**
   - Update `valid_types` list in `validate_report_type()` (line 61)
   - Add Trivy/Vulnix structure validation in `validate_report_structure()` (line 66)
   - Add filename mappings in `save_report()` (line 236)

3. **Update status logic (optional)**
   - Dashboard "OK" logic currently checks for Neofetch + Lynis
   - Consider adding Trivy or Vulnix as acceptable alternatives
   - Document in CLAUDE.md if changed

4. **Test with sample tar archives**
   - Create `test-tar-submit.sh` script with sample tar creation
   - Test error cases: corrupted tar, path traversal, oversized files

5. **Update documentation**
   - Add curl examples to README.md
   - Update CLAUDE.md with new endpoint details
   - Document filename patterns for report type detection

### Rollback Strategy

Since `/submit-tar` is a new endpoint and doesn't modify existing behavior, rollback is simple:
- Remove the new handler code
- Existing clients using POST `/` are unaffected

No data migration needed (filesystem layout unchanged).

## Open Questions

None at this time. Design is ready for implementation.
