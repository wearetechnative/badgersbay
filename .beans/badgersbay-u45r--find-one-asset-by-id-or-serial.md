---
# badgersbay-u45r
title: Find one asset by id or serial
status: todo
type: task
priority: low
created_at: 2026-09-17T14:29:49Z
updated_at: 2026-09-17T14:29:49Z
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
