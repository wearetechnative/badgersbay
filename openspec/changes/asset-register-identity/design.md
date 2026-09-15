## Context

The scanning process is a campaign, not a deadline. A task fires at the start of
an audit month; the owner then works through the asset register over the
following weeks, asking each holder to run the client. The spring 2026 round ran
from 2026-03-26 to 2026-04-22. The current model assumes uploads are filed
against a future deadline, which is why it cannot represent a round in progress.

Eleven assets are in scope, audited twice a year. That is roughly twenty-two
submissions per year. Every design decision below should be read against that
number: the problem is not volume, it is that the data model cannot express the
question being asked.

## Decision: the hardware serial is the identity

The serial is already collected and shipped. `hardware-serial.txt` is present in
every tar produced by the current client on every platform that submits.

Alternatives considered and rejected:

- **Hostname.** Client-controlled and demonstrably drifting. The directory
  `mustad-jumphost-root/` holds system information reporting hostname
  `ip-10-0-0-250`. Windows hostnames are randomly generated at install
  (`LAPTOP-AC06CMEP`).
- **Owner.** Not unique. One person in the register holds three assets.
- **Model.** Not unique. Two identical Framework 13 laptops are in the register.

A submission whose serial is not in the register is stored under
`reports/unmatched/` and surfaced on the dashboard rather than silently
accepted. That is a feature: it catches a new asset, an out-of-scope department,
or a register error.

### A serial is often missing, and that is a state, not an error

Measured across all 22 archives on compute2-prod: five systems carry a usable
serial, and the rest do not.

    FRANMDCPA750850030  lego2-pim                  usable
    PF50L2MR            lobos-wtoorren             usable
    FRANDGCPA5530200H9  Jeroen-jeroen              usable
    PF50L2ML            mathijs-p16s-mathijs       usable
    MP1Y69AC            pankhuri-... (3 archives)  usable

    Not available       SammyMBPro-Sammy
    Not available       technative-casper-casper   (4 archives)
    Not available       nixos-pankhurip            (4 archives)
    "Mac OS X<TAB>"     MBP-van-pim-pim

`dmidecode -s system-serial-number` needs root; without it the Linux client
writes the literal string `Not available` (bean wtoorren-m6ho). The macOS client
writes a fragment of unrelated output (bean wtoorren-5qvb). A virtual machine
may legitimately have no serial at all.

So the system must be designed for a missing serial rather than assuming one.
A submission without a usable serial is stored, surfaced, and counted as a
problem to fix — never discarded and never silently attributed.

**A usable serial** is a single non-empty token containing no whitespace and
matching no known placeholder (`Not available`, `Not available (VM or unknown
hardware)`, `To Be Filled`, `O.E.M.`, `Default string`, `System Serial Number`,
all-zeroes). Everything else counts as absent.

### Two ways a submission fails to resolve, and they need different fixes

    no_serial                 the archive carries no usable serial
                              -> a client problem: the audit ran without root,
                                 or the platform writes the wrong field

    serial_not_in_register    a usable serial that the register does not know
                              -> a register problem: a new asset, an
                                 out-of-scope department, or a wrong column D

Both land in `reports/unmatched/<hostname>-<username>/<timestamp>/` — one tree,
not two — and the record carries which of the two it was. The dashboard keeps
them apart, because telling someone to fix their spreadsheet when their laptop
never reported a serial wastes everyone's time.

### The register is not yet clean

Before the serial can be trusted as a join key, column D of
`iso27001-compliance-essential.xlsx` needs a pass. At least one row is wrong:

| Asset      | Owner     | Register says | Client measures |
|------------|-----------|---------------|-----------------|
| TARI-00031 | Elma Aker | `AC06CMEP`    | `YD063JGA`      |

Pankhuri Prakash measured `MP1Y69AC` where the register holds `PF3NFHJL`. That
one is not an error: the asset was replaced. It is the case the multi-serial
design exists for — two rows under one `asset_id`, each with its own validity
window, and a continuous history across the swap.

`AC06CMEP` is the random suffix of the Windows hostname `LAPTOP-AC06CMEP`, not a
BIOS serial — most likely transcribed from the neofetch banner. `TARI-00034`
(`PF-4VBTLB`) also departs from the Lenovo format seen elsewhere in the sheet
(`PF50L2MR`, `PF3NFHJL`) and should be verified.

This is manual work outside the codebase, and it blocks the register being
authoritative. The unmatched view exists partly so that remaining errors
announce themselves instead of hiding.

## Decision: one record per submission

    reports/
      2026-03/                            frozen archive, existing layout
      submissions/
        PF50L2MR/
          2026-09-15T13-25-34/
            honeybadger-lobos-wtoorren-15-09-2026.tar.gz
            fastfetch.json
            lynis-report.json
        YD063JGA/
          2026-09-15T14-43-16/
            ...
      unmatched/
        LAPTOP-AC06CMEP-elma/
          2026-09-15T14-43-16/

No audit period appears in a path. The period of a submission is computed from
its timestamp and the configured `audit_months`, so changing `audit_months` from
`[3, 9]` to `[3, 6, 9, 12]` reclassifies history correctly instead of leaving
directory names that silently mean something else.

Records are never overwritten. This is what makes the three existing collisions
disappear: `lobos-wtoorren-20260315/lynis-report.json` and
`lobos-wtoorren-20260316/lynis-report.json` are two submissions at two times,
not two candidates for one filename.

## Decision: audit period maps backward, with a late window

    get_audit_period(d, audit_months) -> most recent audit month <= d

    2026-09-15  ->  2026-09    in window, on time
    2026-10-02  ->  2026-09    late, still this round
    2026-04-10  ->  2026-03    late, still the spring round
    2026-02-10  ->  2025-09    late

A submission is **on time** if it arrives within the audit month itself and
**late** if it arrives afterwards but before the next round opens. Both count
toward the round; the distinction is reported, because "asset X was scanned
three weeks after the deadline" is an auditable fact worth keeping.

This rule is what the agreed migration boundary already implies: everything up
to 2026-08-31 belongs to the 2026-03 round.

## Decision: completeness is per platform class

`required_reports: [fastfetch, lynis]` cannot be satisfied on Windows, which has
no Lynis. Two of eleven assets would be permanently red — the fastest way to
teach people to ignore a dashboard.

    class    sysinfo          hardening
    linux    fastfetch.json   lynis-report.json
    macos    fastfetch.json   lynis-report.json
    windows  fastfetch.json   hardeningkitty.csv

The class comes from the register, not from guessing at the submission. Naming
the requirement rather than the tool is the correction promised in
`use-fastfetch-system-info`: the previous model broke precisely because a tool
name was used as a requirement name, and it broke again the moment a platform
arrived with a different tool.

Windows cannot satisfy this yet — `AUDIT.ps1` writes ASCII art rather than
`fastfetch.json`, and does not submit at all. Until `wtoorren-cikq` lands, those
two assets are reported as `manual` rather than as incomplete.

## Decision: two views, one index

    ROUND VIEW                          FLEET VIEW
    "who do I still have to chase"      "how do we stand"

    progress over the register for      latest submission per asset,
    the round that is currently open    regardless of round, with age

Both are queries over the same records. The round view is a LEFT JOIN from the
register: assets with no submission in the open round are rows, which is the
entire point. The fleet view answers the standing question independently of
where we are in the cycle.

No Grafana. Both views are rendered by the server.

## Consequences

`honeybadger_server.py` is 2186 lines. `CLAUDE.md` still describes it as 837 and
lists "adding an authentication system" and "adding a database backend" as
triggers to split the file; the first has already happened and the second is
queued as `wtoorren-634y`. This change adds a register loader and a second
dashboard view. The single-file principle has effectively expired and should be
retired deliberately here rather than eroded further in silence.

## Decision: the register moves, the evidence does not

Re-exporting `assets.csv` after a transfer or a retirement must not rewrite a
closed round. If it does, the March report stops being reproducible: a scan made
on Pim's laptop is attributed to its new holder, and a coverage rate computed
over eleven assets is recomputed over ten.

Two measures, each solving a different half.

**Denormalise at submission time.** When a submission is recorded, `asset_id`,
`owner` and `class` are written into the record rather than joined at read time.
This is the invoice pattern: the address is copied onto the invoice, not looked
up afterwards. Every submission is then self-describing and no register change
can reach backwards.

**Scope membership is computed from validity dates.** An asset belongs to a
round when its in-scope window overlaps that round's scan window. The register
carries `valid_from` and `valid_to` per row, so "who was in scope in March" is a
function of recorded dates rather than of whichever rows exist today. Re-running
the March report a year later gives the same answer without a snapshot file.

An earlier draft froze a copy of the register at round open. That was wrong: a
device stolen on 20 September and replaced on the 22nd must be scanned in the
September round, and a new employee starting mid-round must be too. A frozen
denominator cannot express either. Validity windows give reproducibility without
buying it at the cost of correctness.

## Decision: a round has two windows

Conflating them is what produced the original forward-filing bug.

    round 2026-09
      scan window       2026-09-01 .. 2026-09-30 + grace_weeks
                        the work happens here, and this window decides
                        which assets belong to the round

      coverage window   2026-09-01 .. the next round opens
                        the period the round makes a statement about

`grace_weeks` does double duty, which is the point: it is the boundary between
`on_time` and `late` for a submission, and the boundary for scope membership of
an asset. One configured value, one concept.

    asset enters scope inside the scan window   -> belongs to this round
    asset enters scope after it closes          -> belongs to the next round,
                                                   and shows in the fleet view
                                                   immediately as never audited

The second case matters: a laptop issued in January must not be invisible until
March merely because it missed a window. It is out of scope for the round and
present in the fleet view, which is where the standing question lives.

## Decision: leaving scope mid-round is recorded, not subtracted

An asset that leaves scope during a round — stolen, written off, returned — is
not silently removed from the denominator. Its `valid_to` carries a reason, and
if it left without having been scanned it is counted as accounted-for rather
than as scanned.

Silent subtraction would raise the coverage rate and erase the event. A stolen
laptop is exactly the kind of thing an ISO audit wants to find recorded, not
absent. The three categories from `register-administration` absorb this without
a fourth: a departure with a reason lands in `accounted for`, alongside
exceptions.

## Decision: retirement is explicit, never a missing row

A retired asset stays in the register with `status: retired` and a date. It is
excluded from the round denominator, kept visible in a separate section, and
keeps its history.

Dropping the row instead was rejected. A row that disappears from an export is
indistinguishable from a row that was forgotten, or an export that was filtered
or truncated — and the failure mode is a silently shrinking denominator, which
raises the coverage rate. That is the one direction a compliance number must
never move by accident.

## Decision: asset_id is the identity, serial is the lookup key

The ISO register tracks asset IDs; badgersbay follows it. The hardware serial is
how an incoming submission is matched to an asset, and an asset may have more
than one over its life — a mainboard replaced under warranty, or a replacement
device issued under the same asset ID, changes the serial without changing the
asset.

    asset_id,serial,owner,model,class,status,owner_since,valid_from,valid_to
    TARI-00023,PF50L2MR,Wouter van der Toorren,LENOVO 21K9CTO1WW,linux,active,2024-01-01,2024-01-01,2026-06-01
    TARI-00023,PG81N4QX,Wouter van der Toorren,LENOVO 21K9CTO1WW,linux,active,2024-01-01,2026-06-01,

Two rows, one asset, continuous history. Rare, but cheap to allow now and
expensive to retrofit.

`owner_since` carries a second use. A submission whose `scanned_at` predates the
current holder is evidence about someone else's use of the device, which for a
personal device audit is usually not evidence at all. Whether that forces a
re-scan is a policy question outside this system; that the system can see it is
not.

## Out of scope: how the register reaches the server

This change loads the register from a configured path and does not care how it
got there. Delivery is handled separately in `register-administration`, which
also covers marking assets as excepted for a round.

## Open questions

None outstanding. Earlier open points on excused assets and on archive
reconciliation are resolved: exceptions are covered by `register-administration`,
and the frozen `reports/2026-03/` tree stays unjoined as an archive view, since
it carries no serials and hand-mapping three systems buys nothing the stored tar
archives do not already prove.
