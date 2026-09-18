# A note may sit beside a register row

## Why

`AssetRegister.load()` hands the file straight to `csv.DictReader`, so the first
line is the header whatever it says. A `#` note at the top of `assets.csv`
produces

    assets.csv is missing required column(s): asset_id, class, owner, serial

which names four columns that are present, and sends the reader looking for a
column problem instead of at the line they just wrote. A note further down does
worse: it parses as a data row and fails validation on whichever field it
happens to land in.

The register has since become the record of asset identity
(`2026-09-18-register-owns-asset-identity`). The ISO tool export was read once
and is not a feed; asset numbers are assigned and maintained here, by hand, in a
file that ships as an encrypted agenix secret. That file is never seen in a diff
and never reviewed, so the only place a decision about a row can be recorded is
beside the row - and that is the one thing the format refuses.

The notes are not hypothetical. `TARI-00031` carries `YD063JGA`, read from
`Win32_BIOS` on the machine; the ISO tool holds `AC06CMEP`, which is the suffix
of that machine's hostname. Anyone comparing the register against the tool will
read that row as a typo and fix it, and the asset stops matching its own
submissions. `TARI-00034` carries `PF-4VBTLB` with the hyphen the tool writes,
which at another machine turned out to be decoration the hardware does not
report - a value resting on one reading, which is worth saying out loud. And
three Windows assets sit outside the denominator because `MANUAL_CLASSES` keeps
them there until the client has been verified end-to-end; a reader counting rows
against the dashboard cannot tell that decision from an oversight.

Every one of those is a sentence next to a row. Today writing it down stops the
service from starting.

## What Changes

- Lines whose first non-whitespace character is `#` are dropped before the file
  reaches `csv.DictReader`, so a note may sit above the header and between rows.
  No asset id, serial, owner name or class ever legitimately begins with `#`, so
  nothing is given up for it
- Row numbers in errors stay the line numbers of the file the maintainer opens.
  The notes are counted even though they are not parsed, because an error that
  names a line the editor cannot find is worse than one that names no line
- The error for an unusable header names the line it read and quotes it, rather
  than only listing the columns it wanted. The `#` case that produced it is now
  impossible, but a file that opens with a data row, a stray blank line, or a
  semicolon-separated export still lands here, and the message now points at the
  fault instead of away from it
- `assets.csv.example` carries the comments it was written to have. The commit
  that rewrote it recorded that it carries none "because the format cannot hold
  them"
- The README's register section says the format takes comments

## Impact

- Affected specs: `asset-register`
- Affected code: `honeybadger_server.py` (`AssetRegister.load()`, one new pure
  function), `assets.csv.example`, `README.md`

## Not changed

Comments are read and discarded, not preserved. Nothing in the server writes the
register - it is delivered as a secret and is read-only to the service - so
there is no write path for a comment to survive, and inventing one would be
inventing a feature.

Nothing is parsed out of a comment either: no directives, no key-value metadata,
no structured exception reasons. A note is for the person editing the file. A
fact the service needs belongs in a column, where it is validated.
