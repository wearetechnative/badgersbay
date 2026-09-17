# Tasks

## 1. Name the file

- [x] 1.1 A function that builds the download name from the served path and the
      submission record, with doctests covering a matched asset, an unmatched
      one with a serial, and an unmatched one without
- [x] 1.2 Keep the report type in the name so the files stay distinguishable
- [x] 1.3 Preserve `.tar.gz` as one suffix rather than treating `.gz` as the
      extension

## 2. Use it

- [x] 2.1 Serve every file through it, not only the archive
- [x] 2.2 Leave the legacy `/reports/` route alone; it already prefixes with its
      directory and nothing links to it

## 3. Verify

- [x] 3.1 Doctests and `python3 -m unittest test_asset_inventory`
- [x] 3.2 An end-to-end test that downloads a report and asserts the
      Content-Disposition names the asset and the round
- [x] 3.3 A test that two assets' reports no longer collide
- [x] 3.4 A test for an unmatched submission, which is the case the old code
      named worst
- [x] 3.5 `openspec validate --strict`
