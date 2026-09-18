---
# badgersbay-kgl2
title: Requests standing with the ISO tool administrator
status: completed
type: task
priority: normal
tags:
    - iso
    - register
created_at: 2026-09-17T13:32:40Z
updated_at: 2026-09-18T11:20:26Z
---

Raised while rebuilding the register (`rebuild-asset-register-from-iso-export`).
None of these can be fixed in badgersbay; all of them make the next rebuild
cheaper or the register more correct.

## Fill the `Asset tag` column

The column holds 2 of 51, and inconsistently: `TARI-00037` sits in the column
while `TARI-00023` sits inside the serial field as `PF-50L2MR / TARI-00023`.
The remaining eleven TARI numbers in use were recovered from a compliance
workbook that is regenerated every round, which is the wrong home for a durable
identity.

Filled, the export carries the identity and the next rebuild is a transformation
rather than a conversation. Request already made.

Two assets currently have no number at all in the tool and were assigned one by
hand during this rebuild: `PF50L2ML` as TARI-00022 and `MP1Y69AC` as TARI-00041.
Those need to be recorded in the tool, or the tool and the register already
disagree.

## Correct AC06CMEP

`TARI-00031` holds `AC06CMEP`, which is the random suffix of the Windows
hostname `LAPTOP-AC06CMEP` rather than a hardware serial. The machine reports
`YD063JGA`, read from `Win32_BIOS`. The register now carries the machine's
value; the tool still carries the hostname fragment.

Worth one look at the sticker underneath before changing the tool - the method
was right but it is one reading (`honeybadger-wbq4`).

## Two assigned laptops are unencrypted

`PF2RFH1Z` and `MP1Y69AC`, both issued to Pim Snel in August 2026, both recorded
`Encrypted: No` and both classified Confidential.

This is an ISO finding rather than a register fault, and it is worth saying how
it nearly went unseen: the xlsx export renders that column as a hex colour
(`#ea6153`, `#91cf66`), so the meaning is destroyed on the way out. It was only
visible in the tool's own rendering.

## The export loses more than encryption

`Owner` and `User` come out as entity ids rather than names, so a register built
from the export alone cannot name anybody. Deriving the mapping by joining on
serial resolved 1 of 15 and produced two contradictions, so it is not a
workaround. A person export - entityId plus name - would remove that obstacle
entirely.


## Closed

Reported done on 2026-09-18 and closed as handled. What the outcome was per
item is not recorded here.

The list is kept below so a later reader can see the scope this bean carried:

- Fill the `Asset tag` column in the ISO tool, so the TARI numbers travel in
  the export instead of being recovered from a workbook that is regenerated
  every round.
- Record `TARI-00022` (`PF50L2ML`) and `TARI-00041` (`MP1Y69AC`). Both were
  assigned by hand during the register rebuild and existed only in
  badgersbay's register.
- Correct `AC06CMEP` to `YD063JGA` for `TARI-00031`.
- Report `PF2RFH1Z` and `MP1Y69AC` as recorded `Encrypted: No`.
- Ask for a person export mapping entity ids to names.

Which of these were fulfilled, and in what form, was not written down at the
time. Anyone who needs that should read it from the tool rather than from this
bean.

One thing is worth checking before the next register rebuild: whether the
`Asset tag` column is now populated. Filled, the rebuild is a transformation of
the export; empty, it is another manual reconciliation. This bean does not say
which it will be.
