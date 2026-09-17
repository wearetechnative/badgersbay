# Name every download for the asset it belongs to

## Why

Downloading the evidence behind one asset produces:

    TARI-00023-2026-09-17-wouter.toorren.tar.gz
    lynis-report.json
    fastfetch-report.json

The archive is named for its asset and round. The reports are named for
themselves, and every asset in the fleet produces the same two names. Download a
second asset into the same folder and the first is overwritten, or the browser
appends `(1)` and the reader is left guessing.

The comment above the naming code states the intent: a download should go
straight into the audit folder under the name the compliance sheet expects. That
holds for one of the three files on offer, because the naming is gated on
`.gz`.

A report that has to be renamed by hand before it is evidence is a report
somebody has to be trusted about.

## What Changes

- Every file `/evidence/` serves is named for the asset and the round, not only
  the archive
- The report type is kept in the name, so the files stay distinguishable
- An unmatched submission is named for the identity it does have - its serial,
  or the hostname and username it arrived under - rather than falling back to
  the in-archive name, which is what produces the collision

## Impact

- Affected specs: `report-storage`
- Affected code: `honeybadger_server.py` - the `/evidence/` handler
- The legacy `/reports/` route already prefixes with its directory name and
  nothing links to it; it is left alone.
