# Tasks

## 1. Count the right trees

- [x] 1.1 Walk `submissions/<serial>/<record>/`, `unmatched/<key>/<record>/` and
      the archive period directories in one pass, dropping the mode branch
- [x] 1.2 Take the hostname from `submission.json` where the record has one, and
      parse the directory name only for archive entries
- [x] 1.3 Keep `total_report_directories`, `unique_hosts` and `reports_by_type`
      reporting what their names say

## 2. Report the breakdown

- [x] 2.1 Add `statistics.by_source` with `matched`, `unmatched` and `archived`

## 3. Verify

- [x] 3.1 Doctests and `python3 -m unittest test_asset_inventory`
- [x] 3.2 A test that a real archive submission is counted, which is the
      regression this fixes
- [x] 3.3 A test that an unmatched submission is counted and attributed to
      `unmatched`
- [x] 3.4 A test that a storage tree holding only archive period directories
      still reports them, so the fix does not trade one blind spot for another
- [x] 3.5 `openspec validate --strict`
