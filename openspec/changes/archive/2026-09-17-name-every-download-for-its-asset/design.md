# Design

## The convention is the point, not the tidiness

`proof_file` in the compliance workbook holds values like
`TARI-00023-2026-09-14`. A downloaded file that already carries that name drops
into the audit folder as evidence for a known asset in a known round. One that
has to be renamed first is evidence of whatever the person renaming it says it
is.

So the rule is applied to every file the endpoint serves, and the report type is
appended rather than replacing the convention:

    TARI-00023-2026-09-17-wouter.toorren.tar.gz
    TARI-00023-2026-09-17-wouter.toorren-lynis.json
    TARI-00023-2026-09-17-wouter.toorren-fastfetch.json

Sorting a folder of these groups an asset's evidence together, which is the
order somebody filing it wants.

## Unmatched submissions had a fallback that did not exist

The spec said an unmatched download "falls back to hostname, username and
timestamp". The code did no such thing: with no `asset_id` it kept the file's
own name, so an unmatched archive downloaded as `honeybadger-20260917-142233.tar.gz`
and an unmatched report as `lynis-report.json`.

That is the worst case rather than an edge case. An unmatched submission is a
machine scanning without being credited to any asset - exactly the file somebody
needs to identify - and it was the one with the least identifying name.

It is now named for what it does have. The serial is the better identity when
the client reported one, because that is the value the register will eventually
be matched on; hostname and username are the fallback beneath it.

## One function, not a branch per caller

The naming is a pure function of the served path and the submission record, so
it is one function with doctests rather than logic inline in the handler. The
previous shape - a default assignment, then an `if` that replaced it for one
suffix - is how the archive came to be the only file that followed the rule.
