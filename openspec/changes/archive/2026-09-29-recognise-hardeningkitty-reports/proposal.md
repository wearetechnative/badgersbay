## Why

Windows submissions are always recorded incomplete. The requirement set for class `windows` is
`sysinfo` and `hardening`, where `hardening` is satisfied by a HardeningKitty report
(`report-completeness-validation`), but the tar handler recognises only JSON members named for
lynis, fastfetch, trivy or vulnix. The Windows client sends its hardening audit as
`hardeningkitty.csv`, which is never recognised, so `hardening` is never met.

It went unnoticed because no Windows machine could submit until the Windows client caught up. The
first two fleet submissions from Windows laptops are now in, and both show as incomplete with
`hardening` missing, although their archives carry the report.

## What Changes

- The tar handler recognises `hardeningkitty.csv` as report type `hardeningkitty`, checks it is a
  HardeningKitty result rather than any CSV, and stores it alongside the archive like the other
  reports. The submission's recorded report set includes it, so a Windows submission carrying it
  is complete.
- Records stored before this change are repaired once, from the archive they already hold: a
  record whose stored archive contains a valid `hardeningkitty.csv` that its report set lacks has
  the report extracted and added. Nobody has to submit again.
- The repair is limited to that one case. Records are otherwise not re-processed, and no other
  recorded field - register state, timeliness, the inventory - is touched.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `tar-submission`: HardeningKitty CSV is a recognised report, and previously stored archives are
  re-read for it, once.

## Impact

**Code**
- `honeybadger_server.py`: report type detection, validation and storage for a CSV report; a
  startup repair of stored records.

**Behaviour**
- Windows submissions with a HardeningKitty report count as complete, including those already
  stored. `MANUAL_CLASSES` still keeps Windows out of the round's denominator; taking it out is
  bean `badgersbay-n8g8`, which this unblocks on the server side.
- A record changed by the repair is logged, naming the record and the report added.
