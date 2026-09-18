---
# badgersbay-u45r
title: Find one asset by id or serial
status: completed
type: task
priority: low
created_at: 2026-09-17T14:29:49Z
updated_at: 2026-09-18T11:32:39Z
parent: badgersbay-qeqg
---

Jumping to a single asset without reading the page. The two identifiers people
have at hand are the TARI number, which comes up in conversation, and the
hardware serial, which comes off a sticker or out of a submission.

Lower priority than the state and owner filters: with a fleet of this size,
Ctrl-F does the job. It stops doing the job somewhere around fifty rows.

Matching should be on the serial as the register holds it after normalisation -
`normalise_serial()` uppercases and strips whitespace but leaves separators
alone, so a reader typing a serial with the hyphen the ISO tool writes and a
reader typing it as the machine reports it are looking for different strings.


## Summary of Changes

`q=` matches part of an asset id or a hardware serial.

Both sides are folded by `search_key()`, which removes case and every
non-alphanumeric character. That fold is the whole point: `normalise_serial()`
uppercases and strips whitespace but leaves separators alone, so the serial as
the ISO tool writes it and the same serial as the machine reports it are
different strings in the register. Folded, they are one.

The same fold makes `TARI-00031`, `tari00031`, `00031` and `31` all reach
TARI-00031, which is what a reader with the number in their head will type.

A query of separators alone is no query and is dropped.
