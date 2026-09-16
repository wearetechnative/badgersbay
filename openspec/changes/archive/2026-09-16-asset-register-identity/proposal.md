## Why

The dashboard answers the wrong question. It shows what arrived; compliance is
about who is missing.

Today the system has no notion of which systems are expected to report. A
system that does not submit simply has no directory, so it produces no row —
not a red row, no row at all. On 2026-09-15, mid-way through the September
audit round, the dashboard's default view showed one system: a March test
artifact. The other fifteen directories were in `2026-03` and therefore
invisible, and the eleven assets in the ISO register were nowhere, because the
register is not known to the server.

Three further defects follow from the same root cause — identity and time are
encoded in directory names:

1. **The period label misstates time.** `get_audit_period()` maps an upload
   forward to the next audit month, so `reports/2026-09/` holds everything
   uploaded from April onward. The spring round ran from 2026-03-26 to
   2026-04-22; under the current rule its late submissions were filed into the
   September round. The same cliff is two weeks away: an upload on 2026-10-01
   lands in `2027-03` and drops out of the round it belongs to.
2. **A "complete" set is not a moment.** Completeness counts filenames, not
   times. A Lynis report from April and system info from August satisfy it.
3. **Identity is unstable.** The directory key is `hostname-username`, which the
   client controls and which drifts: `mustad-jumphost-root/` contains system
   info reporting hostname `ip-10-0-0-250`. A reinstall breaks the link.

Meanwhile the client already sends a stable key. Every tar contains
`hardware-serial.txt`. The server discards it along with twelve of the fourteen
files in the archive.

## What Changes

- **Identity becomes the hardware serial**, read from `hardware-serial.txt` in
  the submitted tar. Hostname and username become descriptive, not structural.
- **Introduce an asset register**: `assets.csv`, exported from the ISO
  reporting sheet, mapping serial to asset ID, owner and platform class. The
  register is the denominator; the sheet remains its source.
- **One record per submission, never overwritten.** Submissions are stored
  under `reports/submissions/<serial>/<timestamp>/`. Audit period becomes a
  computed property, not a directory name.
- **Audit period mapping becomes backward-looking**, with a late-but-counted
  window: a submission belongs to the round that was open when it arrived.
- **Two dashboard views** over one index: round progress (who still has to
  submit) and fleet status (latest known state of every asset).
- **Completeness becomes per platform class.** Windows assets have no Lynis
  score; requiring one makes them permanently red.
- **Report types are named after requirements, not tools**: `sysinfo` and
  `hardening`, satisfied by fastfetch and by Lynis or HardeningKitty.

## Capabilities

### New Capabilities
- `asset-register`: load, validate and reconcile the asset register against
  received submissions

### Modified Capabilities
- `audit-period-management`: backward-looking mapping, computed not stored
- `report-storage`: submission-per-timestamp layout keyed on serial
- `report-completeness-validation`: per platform class, requirement-named types
- `compliance-dashboard`: round view and fleet view

## Impact

- **Storage layout changes.** `reports/2026-03/` is frozen in place as the
  archive of the closed spring round. New submissions use the new tree.
- **Clients are unaffected.** No client change is required: the serial is
  already in every tar. Windows is the exception and is tracked separately
  (bean `honeybadger-k80g`).
- **The register must be clean before it can be a key.** Column D of the
  reporting sheet is known to be wrong for at least one asset — see design.
- **Prerequisite**: `use-fastfetch-system-info`.

## Non-goals

- Extracting compliance columns (disk encryption, screen lock, firewall,
  hardening score) from submissions. That needs a machine-readable summary from
  the client; see the honeybadger change `emit-asset-inventory-json`. This
  change establishes identity and the register, which that work depends on.
- Moving the index into PostgreSQL. See bean `badgersbay-8ylz`.
