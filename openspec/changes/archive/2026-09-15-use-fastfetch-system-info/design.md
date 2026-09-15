## Context

Three naming layers are in play:

| Layer                 | Linux            | macOS (current)  | macOS (legacy) | Windows      |
|-----------------------|------------------|------------------|----------------|--------------|
| client tool           | fastfetch        | fastfetch        | neofetch       | neofetch     |
| file in tar           | `fastfetch.json` | `fastfetch.json` | `neofetch.json`| `neofetch.txt` |
| server accepts        | no               | no               | yes            | no           |

`RUNME.sh` runs the same fastfetch block for Linux and macOS (`uname -o`
branches at line 53 only for platform-specific collection elsewhere), so the
current client emits `fastfetch.json` on both. Windows (`AUDIT.ps1:135`) still
runs neofetch and writes ASCII art, which was never parseable and is out of
scope here — see bean `honeybadger-k80g`.

## Decision: finish the extraction before renaming anything

Renaming the detection function changes nothing on its own. Tar submitters
never reach it, and they are the only submitters that matter here — the
honeybadger client bundles and uploads, it does not POST one report at a time.
A change that only renamed would ship a correct spec describing a code path
nobody uses, while the September round kept recording every Linux asset as
incomplete.

This is not scope growth. `2026-03-26-submit-tar-feature` specified extraction
and per-file status, was archived as delivered, and left
`extract_and_validate_tar()` with zero call sites. The capability spec that
would have caught it, `tar-submission`, never landed in `openspec/specs/` —
the same root cause as the delta-header repair: a spec that cannot be parsed
or does not exist cannot contradict the code. This change finishes that work
and lands the spec.

The two defects also cannot be separated in either order:

    wire extraction first    every Linux tar contains fastfetch.json, which
                             has no recognised type, and line 738 rejects the
                             whole archive -> HTTP 400 for all six assets

    rename first             nothing calls the renamed function; the round
                             stays broken

So: one change, extraction and naming together.

### Unrecognised members must not reject the archive

`extract_and_validate_tar():738` returns a hard failure when any JSON member
has no recognised report type. That is wrong for a format the client will keep
extending: a single unknown file would reject a submission whose known reports
are perfectly good, and the operator would see a 400 with no evidence stored.

The archived spec already called for HTTP 207 Multi-Status with per-file
status. That is the behaviour: recognised reports are saved, unrecognised JSON
members are reported, and the tar is stored whole either way.

### The tar is still stored whole

Extraction is additive. The archive is the evidence an auditor receives, and
`asset-register-identity` will read `hardware-serial.txt` out of it. Nothing
about this change removes or replaces the stored archive.

## Decision: one name, not a compatibility shim

Accepting both `fastfetch.json` and `neofetch.json` was considered and rejected.
The root cause of this bug is that a *tool name* was baked into the data model:
`required_reports: [neofetch, lynis]` is a list of tools presented as a list of
requirements. Accepting two tool names doubles that mistake rather than
correcting it.

A fuller correction would name the requirement after what it is — `sysinfo` and
`hardening`, satisfied by fastfetch and by Lynis or HardeningKitty per platform.
That is the right end state and it is what makes the Windows assets fit without
a special case. It is deliberately not done here: this change must be small
enough to ship during a running audit round. The rename is recorded as the
follow-up in `asset-register-identity`.

## Decision: legacy files are archive, not input

`neofetch-report.json` files already on disk are left untouched. Renaming them
to `fastfetch-report.json` would misstate their provenance, and a read-time
alias would keep the legacy name alive in exactly the code path this change
exists to simplify. Since all data up to 2026-08-31 belongs to the closed
2026-03 round, and the evidence of record for that round is the stored tar
archives, losing dashboard rendering for those loose JSON files costs nothing
that matters.

## Deferred: the legacy directory merge

The agreed rule is that everything up to 2026-08-31 belongs to audit period
2026-03. One part of that is safe today; the rest is not.

    2026-09/future-test-testuser/  submission-20260326-152038.tar.gz
         -> 2026-03/future-test-testuser/                  no conflict

    lobos-wtoorren-20260315/        lynis-report.json     \
    lobos-wtoorren-20260316/        lynis-report.json      >  all three target
                                    neofetch-report.json   |  2026-03/lobos-wtoorren/
                                    vulnix-report.json    /

    testserver01-testuser-20260316/ lynis-report.json     -> collides with the
                                    trivy-report.json        existing file

Three collisions on `lynis-report.json`. In the current layout the filename
carries no timestamp, so merging means choosing one scan and discarding the
other. Under the model in `asset-register-identity` — one record per submission,
keyed on serial and scan time — these are not collisions at all: the scans of
15, 16 and 26 March coexist.

Only the conflict-free move is done here. It is the part with an operational
reason to happen now: it empties `reports/2026-09/`, so the dashboard's default
view stops showing a March test artifact as the sole system of the September
round.

## Risks

- **Status changes on next submission, not retroactively.** Systems recorded
  incomplete because nothing was read become complete or incomplete on their
  real contents only when they next submit. Tars already on disk are not
  re-processed, so the 2026-03 period keeps its current figures.
- **Extraction is now on a hot path that was never exercised.** The validation
  it performs - path traversal, symlinks, nesting depth, 50MB archive, 10MB per
  file, 100 members - has never run against a real client archive. Test with
  an actual honeybadger tar, not a hand-rolled one.
- **Config and code must move together.** If `config.yaml` still says
  `mandatory: [neofetch, lynis]` after restart, every system is permanently
  incomplete. Task order reflects this.
