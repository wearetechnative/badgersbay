## 1. Exception records

- [x] 1.1 Store as `reports/exceptions/<period>/<asset_id>.json` with
      `asset_id`, `audit_period`, `reason`, `marked_by`, `marked_at`
- [x] 1.2 Reason is required; reject an empty or whitespace-only reason
- [x] 1.3 Load exceptions during the index rebuild
- [x] 1.4 A submission in the same round supersedes the exception

## 2. Round arithmetic

- [x] 2.1 Three categories: scanned, excepted, outstanding
- [x] 2.2 Round is closeable at `outstanding = 0`
- [x] 2.3 Excepted assets never counted as scanned anywhere in the display

## 3. Dashboard control

- [x] 3.1 Control on each outstanding row: mark excepted, with a reason field
- [x] 3.2 POST endpoint behind the existing dashboard basic auth
- [x] 3.3 Withdraw an exception
- [x] 3.4 Show reason, who marked it and when; label `marked_by` as
      self-reported

## 4. Register delivery via agenix

- [x] 4.2 badgersbay: `--asset-register` argument and config key
- [x] 4.3 Refuse to start on a structurally invalid register: duplicate active
      serial, unknown class, unknown status, overlapping validity for one serial
- [x] 4.4 Retain the previously loaded register on disk so a shrink can be
      detected across a restart
- [x] 4.5 On a smaller register, start and report the disappeared assets
      prominently on the dashboard; never fail silently, never refuse to start

## 6. Verify

- [x] 6.1 Mark excepted, confirm the count moves from outstanding to excepted
      and not to scanned
- [x] 6.2 Submit for an excepted asset, confirm the submission wins
- [x] 6.3 Open the next round, confirm no exception carries over
- [x] 6.4 Exception survives an index rebuild
- [x] 6.5 Deploy a structurally invalid register, confirm the service refuses
      to start with a message naming the fault
- [x] 6.6 Deploy a register missing two assets, confirm the service starts and
      names them
