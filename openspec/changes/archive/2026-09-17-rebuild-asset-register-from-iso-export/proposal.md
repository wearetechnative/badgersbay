# Rebuild the asset register from the ISO tool export

## Why

The register the server runs on holds four rows. The fleet is thirteen assets
across eleven people. Everything not in the register is invisible: it is not
counted as outstanding, and a submission from it lands as
`serial_not_in_register`. So the coverage figure on the dashboard is measured
against a third of the fleet, and nothing on the page says so.

One of those four rows cannot match at all. `TARI-00031` carries `AC06CMEP`,
which is the random suffix of the Windows hostname `LAPTOP-AC06CMEP`. The
machine reports `YD063JGA`. That asset would read as outstanding forever, no
matter how diligently its owner scanned.

A register this small was right while the model was being built. It is the
wrong thing to measure a real round against.

## What Changes

- Rebuild `assets.csv` from the ISO tool's asset export, cross-referenced with
  the `Active Assets` sheet of the compliance workbook
- Thirteen assets, eleven people; ten in the denominator and three Windows
  machines outside it
- Real issue dates from the tool replace the `2024-01-01` placeholder that every
  current row carries
- Correct `TARI-00031` to the serial the machine reports
- Correct `MP1Y69AC`: it is Pim Snel's, not Pankhuri Prakash's, and it is a
  distinct asset rather than a replacement for hers
- Record what belongs in the register at all, as a requirement rather than as
  the result of whoever last edited the file

## Impact

- Affected specs: `asset-register`
- Affected code: none. This is register content and the rule that governs it.
- Affected operations: the register is delivered as an agenix secret, so this
  lands through `ragenx` and a deploy, not through a merge.
