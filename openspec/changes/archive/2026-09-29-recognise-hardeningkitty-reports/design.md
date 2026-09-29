## Context

See `proposal.md` - Why. The requirement is in `specs/`.

```
 Windows archive                     tar handler                         record
 ───────────────                     ───────────                         ──────
 fastfetch.json       ──▶ 'fastfetch'        ✓                reports: [fastfetch]
 hardeningkitty.csv   ──▶ (no rule, not JSON) ✗ unrecognised   → windows needs hardening
 asset-inventory.json ──▶ inventory                              → incomplete
```

`detect_report_type_from_filename()` matches only `*.json`, and `extract_and_validate_tar()` runs
`json.loads()` on every recognised member. A CSV report needs a rule and a path that does not parse
it as JSON. The requirement side already exists: `REQUIREMENT_SATISFIED_BY['windows']['hardening']`
is `('hardeningkitty',)`.

## Goals / Non-Goals

**Goals**
- A Windows submission carrying `hardeningkitty.csv` is complete, when it arrives and after the fact.
- The records already stored become complete without anyone submitting again.

**Non-Goals**
- Reading HardeningKitty findings into the dashboard. The report is recognised and kept, not
  interpreted; the client's own summary of it already travels in `asset-inventory.json`.
- Taking Windows out of `MANUAL_CLASSES`. That is `badgersbay-n8g8`.
- A general re-processing mechanism for stored archives.

## Decisions

### Recognising the report

`hardeningkitty.csv` by basename, case-insensitively, the name the Windows client writes. A member
is accepted as the report when its first line - after a byte order mark, which the Windows client's
files may carry - names at least `ID`, `Category`, `Name`, `Severity`, `Result` and `Recommended`.
Anything else under that name is reported as unrecognised with the reason, the same way an
unparseable JSON report is. The check is on the header only; the rows are HardeningKitty's.

Stored as `hardeningkitty.csv` beside the archive, byte for byte. `REPORT_FILENAMES` gains
`'hardeningkitty': 'hardeningkitty.csv'`, so a download of it is named like the other reports.

### Repairing stored records

The spec says stored archives are not re-processed, so that a closed round keeps the figures it had.
This is the one exception, and it is safe to make because it can only add a report the archive
provably contained: what the archive held has not changed, only what the server can read in it.

At startup, before the index is built, the server walks `submissions/` and `unmatched/`. For a
record whose `reports` lack `hardeningkitty` and whose `evidence` archive is present, it looks for a
valid `hardeningkitty.csv` in that archive by the same rule as above. When there is one, it writes
the file beside the archive and rewrites `submission.json` with `hardeningkitty` added to `reports`
- through a temporary file and a rename, so an interruption leaves the old record whole. No other
field is touched: register state, timeliness and the inventory stay as recorded.

Only Windows records are considered: class `windows` from the register, or an `os_type` naming
Windows for a record that was not matched. Every Linux record lacks this report by design, and
without that filter each start would open every Linux archive. It is idempotent - a repaired record
lacks nothing - so after the first start the only archives opened are those of Windows records that
genuinely carry no HardeningKitty report. Each repair is logged with the record directory.

**Alternative considered:** derive `reports` from the stored archive at read time, for every record.
Rejected - it puts archive reads on every index build, and makes the recorded report set a cache
that may disagree with what the server reads. A one-off repair keeps `submission.json` the single
record of what arrived.

## Risks / Trade-offs

**A closed round's figures change.** A round in which a Windows asset was incomplete will show it
complete after the repair. That is a correction of a server bug, not of what was submitted; but it
applies to rounds that may already have been reported. The log line names every record affected.

**The rename is not atomic across filesystems.** The temporary file is written in the record
directory itself, so the rename stays on one filesystem.
