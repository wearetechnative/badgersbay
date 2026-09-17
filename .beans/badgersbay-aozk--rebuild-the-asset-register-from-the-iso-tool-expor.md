---
# badgersbay-aozk
title: Rebuild the asset register from the ISO tool export
status: todo
type: feature
priority: high
tags:
    - register
    - iso
created_at: 2026-09-17T13:06:28Z
updated_at: 2026-09-17T13:06:28Z
---

OpenSpec change: `rebuild-asset-register-from-iso-export`.

The register the server runs on holds four rows against a fleet of thirteen
assets and eleven people, and one of those four cannot match anything:
`TARI-00031` carries `AC06CMEP`, the random suffix of the Windows hostname
`LAPTOP-AC06CMEP`, while the machine reports `YD063JGA`.

Rebuilt from the ISO tool's asset export cross-referenced with the `Active
Assets` sheet of the compliance workbook. Thirteen rows, ten in the denominator,
three Windows machines outside it.

## The three filters, recorded so nobody re-argues them each round

    51  assets in the ISO tool
    -24  not endpoints        TVs, printers, WiFi points, cameras, phones
    -9   assigned to nobody   laptops in stock
    -5   outside ISO scope    another department
    ---
    13  in the register

The five outside scope are Berry Reijseger, Daniël van Balen, Hamza Benjelloun,
Peter van der End and Remko Franke. Four are classified Confidential, so this is
a scope decision and not an oversight - worth stating, because anyone counting
eleven people against the company's laptop count will otherwise assume something
was forgotten.

## Two corrections to what we believed

`MP1Y69AC` is Pim Snel's, not Pankhuri Prakash's. The register modelled
`TARI-00037` as "Pankhuri's laptop, whichever one that is", with `PF3NFHJL`
replaced by `MP1Y69AC`. The tool says `PF3NFHJL` carries `TARI-00037` and was
issued to her on 2026-06-03, while `MP1Y69AC` went to Pim on 2026-08-10. She
never swapped; a different device changed hands. It becomes `TARI-00041`.

Every row carried `2024-01-01` as `owner_since`. The tool has real issue dates
and they are used. Two land inside the running round, which is the first real
test of the validity windows and `grace_weeks`.

## The finding behind the change

TARI numbers live nowhere. The ISO tool's `Asset tag` column holds 2 of 51, and
inconsistently - one in the column, one inside the serial field. The other
twelve live in a workbook that is regenerated every round, which is the wrong
home for a durable identity. The request to fill that column is with the ISO
tool administrator.

`assets.csv` must not become the home: badgersbay would become a second issuer
of TARI numbers, the two would drift, and the file ships as an encrypted secret
nobody can consult.
