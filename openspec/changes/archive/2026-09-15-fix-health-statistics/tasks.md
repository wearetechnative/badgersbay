## 1. Statistics

- [x] 1.1 `get_health_status()`: branch on `compliance_enabled` and walk
      `reports/<period>/<system>/` in compliance mode
- [x] 1.2 Skip directories that do not match the period shape when scanning in
      compliance mode, so stray entries are not counted as periods
- [x] 1.3 `total_report_directories` counts system directories in both modes
- [x] 1.4 `unique_hosts`: parse `hostname-username` in compliance mode,
      `hostname-username-yyyymmdd` in legacy mode
- [x] 1.5 `reports_by_type` counts system directories holding each report file

## 2. Verify

- [x] 2.1 Against the compute2 storage shape: 16 system directories,
      16 lynis, 1 fastfetch, non-zero unique hosts
- [x] 2.2 Legacy mode still reports the same numbers it did before
- [x] 2.3 Empty storage reports zeros without error
- [x] 2.4 Storage containing only period directories and no systems reports
      zero systems, not zero periods
