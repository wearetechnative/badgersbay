---
# badgersbay-8ylz
title: 'badgersbay: move the index to PostgreSQL'
status: todo
type: epic
priority: normal
tags:
    - badgersbay
    - psql
    - iso27001
created_at: 2026-09-15T21:17:18Z
updated_at: 2026-09-15T21:17:18Z
---

Replace the in-memory `ComplianceCache` with a PostgreSQL index, so the latest
state of every asset and the history per asset become queryable.

A PostgreSQL server is already running; only a database needs creating.

## Premise: the index is derived

The filesystem stays the source of truth. `reports/` holds the evidence an
auditor receives; the database is a rebuildable index.

    POST /submit-tar
          |
          +--> reports/<...>/          ALWAYS FIRST. On failure -> 500.
          |
          +--> INSERT INTO submission  On failure -> log, 200, reindex later.

If the database is down the portal keeps accepting submissions. That is not
negotiable: during a scan round the intake must not close because a database is
restarting.

`--reindex` rebuilds the database from `reports/`. That is the same logic as the
current `ComplianceCache.rebuild()`, with a different destination.

## Schema (rough)

    asset (           -- from assets.csv, export of the ISO register
      asset_id, serial, owner, model, class, active )

    submission (      -- one row per submission, never overwritten
      serial, scanned_at, uploaded_at, hostname, username, client_version,
      os, model, encryption, screenlock, firewall, vuln_packages,
      hardening_tool, hardening_score, os_uptodate,
      evidence_path,  -- path to the tar on disk
      raw jsonb )     -- the whole asset-inventory.json

Two properties that matter:

- **Never overwrite.** One row per submission gives history per asset.
- **`raw jsonb`.** The full summary goes in, so fields not modelled today are
  not lost. The client runs ahead of the server and will keep doing so.

## Absence detection

Assets that submitted nothing must still produce a row. The whole progress
measurement turns on that:

    SELECT DISTINCT ON (a.asset_id)
           a.asset_id, a.owner, s.scanned_at, s.hardening_score
    FROM asset a LEFT JOIN submission s USING (serial)
    ORDER BY a.asset_id, s.scanned_at DESC NULLS LAST;

## Presentation

No Grafana. Badgersbay renders both views itself, over the same table:

- **Round view** - progress within the open scan round, who still has to submit
- **Fleet view** - latest known state per asset, regardless of round

## Consequences

- New dependency: `psycopg2-binary`. Until now only PyYAML.
- Connection string in `config.yaml`; no credentials in the repository.
- Deployment is no longer "copy one file".

## Dependencies

This epic has little value until the data model is keyed on serial:

1. fastfetch only in badgersbay and honeybadger - done
2. read `assets.csv`: serial -> asset_id + owner - done in
   `asset-register-identity`
3. clean up column D of the reporting sheet (honeybadger-wbq4, honeybadger-ck4l)
4. Windows produces machine-readable output (honeybadger-k80g)
