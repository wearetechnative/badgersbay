# Migration Guide: Removal of Trivy and Vulnix Support

## Breaking Change

**Version:** Post-March 2026
**Impact:** High - Breaking change for clients submitting Trivy or Vulnix reports

## What Changed

Honeybadger Server has removed support for Trivy and Vulnix report types to focus on ISO compliance requirements. Only **Lynis** and **Neofetch** reports are now accepted.

### Removed Report Types
- ❌ **Trivy** - Container/OS vulnerability scanner
- ❌ **Vulnix** - NixOS-specific vulnerability scanner

### Still Supported
- ✅ **Lynis** - System hardening audit (required)
- ✅ **Neofetch** - System information (required)

## Why This Change

For ISO compliance auditing, only Lynis (system hardening) and Neofetch (system identification) are required. Trivy and Vulnix added unnecessary complexity for this use case.

## Impact on Existing Deployments

### Server-Side
- **Existing Trivy/Vulnix files on disk:** Remain untouched (data preserved)
- **Dashboard:** Will no longer display Trivy/Vulnix reports
- **Health endpoint:** No longer includes Trivy/Vulnix in statistics
- **New submissions:** Trivy/Vulnix reports will be **rejected with HTTP 400**

### Client-Side
- **Clients submitting Trivy reports:** Will receive HTTP 400 errors
- **Clients submitting Vulnix reports:** Will receive HTTP 400 errors
- **Error message:** `Invalid report type 'trivy'. Supported types: lynis, neofetch`

## Migration Steps

### For System Administrators

1. **Identify affected clients:**
   ```bash
   # Check server logs for current Trivy/Vulnix submissions
   grep -E "(trivy|vulnix)" server.log
   ```

2. **Update client scan scripts:**
   - Remove Trivy scan and submission commands
   - Remove Vulnix scan and submission commands
   - Ensure Lynis and Neofetch submissions remain

3. **Update configuration:**
   - Edit `config.yaml` to remove Trivy/Vulnix from `required_reports.one_of`:
     ```yaml
     required_reports:
       mandatory:
         - neofetch
         - lynis
       one_of: []  # Empty - no additional scanners required
     ```

4. **Deploy updated server:**
   ```bash
   # Backup current version
   cp honeybadger_server.py honeybadger_server.py.backup

   # Deploy new version
   # (copy updated honeybadger_server.py)

   # Restart server
   pkill -f honeybadger_server.py
   ./honeybadger_server.py
   ```

5. **Verify operation:**
   ```bash
   # Test Lynis submission (should succeed)
   curl -X POST http://localhost:7123/ \
     -H "X-Report-Type: lynis" \
     -d @test-lynis-report.json

   # Test Trivy submission (should fail with HTTP 400)
   curl -X POST http://localhost:7123/ \
     -H "X-Report-Type: trivy" \
     -d @test-trivy-report.json
   ```

### For Client Scripts

**Before (with Trivy):**
```bash
#!/bin/bash
# Run scans
lynis audit system --quick
trivy image --format json ubuntu:22.04 > trivy-report.json

# Submit reports
curl -X POST http://server:7123/ \
  -H "X-Report-Type: lynis" \
  -d @/var/log/lynis-report.json

curl -X POST http://server:7123/ \
  -H "X-Report-Type: trivy" \
  -d @trivy-report.json
```

**After (Trivy removed):**
```bash
#!/bin/bash
# Run scans
lynis audit system --quick

# Create neofetch report
cat > neofetch-report.json <<EOF
{
  "host": "$(hostname -s)",
  "hostname": "$(hostname)",
  "os": "$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')",
  "kernel": "$(uname -r)"
}
EOF

# Submit reports
curl -X POST http://server:7123/ \
  -H "X-Report-Type: lynis" \
  -d @/var/log/lynis-report.json

curl -X POST http://server:7123/ \
  -H "X-Report-Type: neofetch" \
  -d @neofetch-report.json
```

## Rollback Plan

If you need to rollback:

1. **Stop the server:**
   ```bash
   pkill -f honeybadger_server.py
   ```

2. **Restore backup:**
   ```bash
   cp honeybadger_server.py.backup honeybadger_server.py
   ```

3. **Restart:**
   ```bash
   ./honeybadger_server.py
   ```

All data remains on disk, so no data loss occurs during rollback.

## Data Retention

**Existing Trivy/Vulnix report files are NOT deleted.**

- Files remain in `reports/` directories
- Can be manually recovered if needed
- Not displayed in dashboard
- Not included in health statistics

To manually clean up old Trivy/Vulnix files:
```bash
# Preview what would be deleted
find reports/ -name "trivy-report.json" -o -name "vulnix-report.json"

# Delete (after verification!)
find reports/ -name "trivy-report.json" -delete
find reports/ -name "vulnix-report.json" -delete
```

## FAQ

**Q: What happens to systems that previously required Trivy or Vulnix?**
A: They are now marked as complete with just Neofetch + Lynis.

**Q: Can I still manually inspect old Trivy/Vulnix reports?**
A: Yes, files remain on disk in their original directories.

**Q: Will the health endpoint still show Trivy/Vulnix counts?**
A: No, only `lynis` and `neofetch` appear in `reports_by_type`.

**Q: Can I re-enable Trivy/Vulnix support?**
A: Not without code changes. If needed, rollback to the previous version.

## Support

For issues or questions:
- Check server logs: `tail -f server.log`
- Review error messages from failed client submissions
- Verify config.yaml reflects new requirements
