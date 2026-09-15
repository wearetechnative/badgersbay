## Why

`/health` reports zero for every statistic on a compliance-mode install.
Measured on compute2-prod:

| Field                      | Reported | Actual |
|----------------------------|----------|--------|
| `total_report_directories` | 2        | 16     |
| `unique_hosts`             | 0        | 16     |
| `reports_by_type.lynis`    | 0        | 16     |
| `reports_by_type.fastfetch`| 0        | 1      |

`get_health_status()` walks one level of the storage directory and looks for
report files there:

    for item in storage_path.iterdir():          # item = "2026-09"
        if (item / 'lynis-report.json').exists() # reports/2026-09/lynis-report.json

In compliance mode reports live one level deeper, under
`reports/<period>/<hostname-username>/`. The loop is written for the legacy
layout `reports/<hostname>-<username>-<yyyymmdd>/`, and `unique_hosts` parses
directory names in that same legacy shape — on `"2026-09"` it yields nothing.

So the endpoint counts audit periods and calls them reports, reports zero hosts,
and reports zero of every report type while sixteen sets sit on disk.

This predates the fastfetch rename; that change only altered which key is
reported as zero. `/health` is the only unauthenticated endpoint and exists for
monitoring, so silently returning zeros is worse than returning nothing.

## What Changes

- Count systems, not audit periods: in compliance mode walk
  `reports/<period>/<system>/`, in legacy mode keep walking
  `reports/<system>/`
- Derive `unique_hosts` from `hostname-username` in compliance mode and from
  `hostname-username-yyyymmdd` in legacy mode
- `total_report_directories` counts system directories in both modes
- Correct the health-monitoring spec, which currently describes only the legacy
  layout and presents it as the whole contract

## Capabilities

### Modified Capabilities
- `health-monitoring`: statistics are computed per storage mode

## Impact

- Monitoring consumers that alert on these numbers have been seeing zeros; after
  this they see real counts. Anything calibrated against zero needs revisiting.
- No change to the response shape, only to the values.

## Non-goals

- The storage layout itself. `asset-register-identity` replaces it with
  submissions keyed on serial; this change makes the endpoint honest about the
  layout that exists today.
