# Design

## Three filters decide what is in the register

The ISO tool holds 51 active assets. Ten of them belong in the denominator. The
distance between those two numbers is the whole design, and each step of it is
a rule someone could otherwise re-litigate every round.

    51  assets in the ISO tool
    -24  not endpoints          TVs, Apple TVs, printers, WiFi points,
                                cameras, Sonos, a 3D printer, phones, a router
    -9   assigned to nobody     laptops in stock
    -5   outside ISO scope      another department's laptops
    ---
    13  in the register
    -3   Windows                outside the denominator until the client can submit
    ---
    10  measured this round

**Not an endpoint.** A television cannot run the audit. It is a real asset and
it belongs in the ISO inventory; it does not belong in a register whose purpose
is to say who has not been scanned. Including it would also break startup:
`VALID_ASSET_CLASSES` is `{linux, macos, windows}` and the loader refuses a
class it does not know.

**Assigned to nobody.** Nine laptops in the tool have no user. A laptop in a
cupboard cannot be scanned and has no one to ask. Counting it as outstanding
produces a permanently red row that nobody can act on, which is the fastest way
to teach people to ignore the dashboard - the same reasoning that put Windows
in `MANUAL_CLASSES`.

**Outside ISO scope.** Five assigned laptops belong to a department that does
not fall under ISO: Berry Reijseger, Daniël van Balen, Hamza Benjelloun, Peter
van der End, Remko Franke. Four of the five are classified Confidential, so
this is a scope decision and not an oversight - recorded here because a reader
counting eleven people against a company with more laptops will otherwise
assume something was forgotten.

## Where TARI numbers live

They live nowhere, and that is the finding behind this change.

| Place | What it holds |
|---|---|
| ISO tool, `Asset tag` column | 2 of 51 filled, and inconsistently: `TARI-00037` in the column, `TARI-00023` inside the serial field |
| Compliance workbook | 12 numbers - but that workbook is a per-round audit report |
| `assets.csv` | whatever was last typed into it |

So a durable identity currently lives in a document that is regenerated every
round. The home should be the ISO tool's `Asset tag` column: the tool already
owns assets, the field already exists, and an export then carries the number
without anyone transcribing it. That request is already with the ISO tool
administrator.

`assets.csv` must not become the home. badgersbay would turn into a second
issuer of TARI numbers alongside the tool, the two would drift, and the file is
delivered as an encrypted secret on a server - the worst place to look something
up.

## TARI identifies the asset, not the person's slot

The current register models `TARI-00037` as "Pankhuri's laptop, whichever one
that is", with two rows: `PF3NFHJL` until 2026-08-01, then `MP1Y69AC`.

The tool says otherwise. `PF3NFHJL` carries `Asset tag TARI-00037` and was
issued to Pankhuri Prakash on 2026-06-03; `MP1Y69AC` was issued to Pim Snel on
2026-08-10 and its description reads "was van Pankhuri". Pankhuri never swapped
machines. A different device changed hands.

So the two-row construction is removed and `MP1Y69AC` becomes `TARI-00041` in
its own right. A serial history on one `asset_id` remains the right model for a
machine whose mainboard is replaced; it is the wrong model for a machine that
moves between people.

## Serials as the tool writes them, except where the machine disagrees

The register is matched on what a machine reports. Where the tool and a machine
disagree, the machine wins, because the machine is what will be submitting.

`TARI-00031` moves from `AC06CMEP` to `YD063JGA`. `AC06CMEP` is the suffix of
the hostname `LAPTOP-AC06CMEP`, which Windows generates at install from
randomness; `AUDIT.ps1` read `YD063JGA` from `Win32_BIOS` on the machine itself.

`TARI-00034` keeps `PF-4VBTLB`, with its hyphen, and this is a known risk rather
than a decision. The tool writes `PF-50L2MR` for Wouter's machine, which
reports `PF50L2MR` - the hyphen is the tool's decoration. `normalise_serial()`
strips whitespace and uppercases but leaves hyphens alone, so a mismatch here
would not match. Richard's machine runs Windows and cannot submit yet, so the
answer cannot be obtained today.

## Dates

Every current row carries `2024-01-01`, a placeholder from when no dates were
available. The tool has real issue dates, and they are used.

Two of them land inside the running round: `TARI-00001` on 2026-08-14 and
`TARI-00041` on 2026-08-10. Assets entering scope mid-round are exactly what
the validity windows and `grace_weeks` were built for, and this is the first
register that exercises them with real data.
