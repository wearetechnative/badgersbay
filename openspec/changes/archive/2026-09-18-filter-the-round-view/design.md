# Design

## A filter must never move a compliance figure

`1 of 10 assets scanned` is a statement about the round. If filtering to
"outstanding" also recomputed it to `0 of 9`, the number on the page would
depend on what the reader happened to be looking at - and somebody would
eventually screenshot it into an audit file.

The defence is structural rather than careful. `compute_round_state()` is never
told about the filter. The round view computes the summary, the meter, the
per-owner bars and the alerts from the state it returns, and only then calls
`filter_round_state()` to produce a second object which nothing but
`_round_table()` ever sees. There is no code path where a filter reaches a
figure, because the figures are rendered before the filtered object exists.

A test pins it: the summary block is captured under no filter and asserted
byte-identical under every filter in turn.

## A query parameter, not a script

The legacy dashboard filtered with JavaScript and its `Show` control needed
fixing in two separate changes. This is a plain `<form method="get">`, the same
decision the round selector already made.

A query parameter survives a reload, can be pasted into a message to the person
who owes a scan - which is the main thing anyone would do with a filter here -
and can be tested by parsing HTML rather than by driving a browser.

It composes with `period=`, which the view already honours, so a filtered view
of a closed round is a link rather than a sequence of clicks. The round selector
carries the active filter as hidden fields, so changing the round keeps the
question you were asking.

The spelling agrees with the round selector that landed in
`2026-09-18-reach-earlier-rounds`: `/?view=round&period=<round>` plus `state=`,
`owner=`, `class=` and `q=`.

## Four terms, and what each one matches

**`state=`** is a closed vocabulary, because the buckets are:
`scanned`, `accounted`, `outstanding`, `unexplained`, `manual`, `retired`.
`accounted` covers both resolved-without-evidence buckets - a recorded exception
and a departure with a reason - because they read as one section in the table
and as one segment in the meter. They stay apart in the data for the reason they
always did; only the filter joins them.

A value outside the vocabulary is not honoured. It is dropped and reported in
the notice, rather than matching nothing: a typo in a URL should show the round,
not an empty page that reads exactly like a finished one.

**`owner=`** matches the value in the register, case-insensitively, not a slug.
`owner_to_slug()` exists to name proof files; it is deliberately lossy about
name infixes and two owners can share a slug, so it is not an identity. The
literal `unassigned` matches a register row with no owner, which is what the
progress panel already calls that case.

**`class=`** matches the register's class. It matters because Windows sits
outside the denominator until its client can submit, so "show me the Linux
machines" is how somebody reads the part of the fleet that is measurable now.

**`q=`** matches the asset id or the hardware serial, on a key with every
non-alphanumeric character removed from both the query and the value. This is
the whole point of the term: `normalise_serial()` uppercases and strips
whitespace but leaves separators alone, so a reader typing the serial with the
hyphen the ISO tool writes and a reader typing it as the machine reports it are
looking for different strings. Folding separators away makes both find the
asset. The same fold makes `31`, `00031` and `TARI-00031` all reach TARI-00031.

Owner, class and text apply across every section; state chooses which sections
survive. A term that matches nothing is a legitimate answer - "Pim owes nothing
in this round" - and the notice is what keeps it from being read as an empty
round.

## An empty table under a filter is not an empty round

Those mean opposite things: one is nobody matching the question, the other is
nothing to do. The view therefore says, whenever any filter is active, what the
filter is, how many of the round's assets it is hiding, and offers a link back
to the whole round.

The notice appears even when the filter hides nothing. A shared link with a
filter that happens to match everything would otherwise be read as the full
picture.

## The owner bars become links

They already look pressable and already carry the per-owner count, so they link
to that owner's filtered view. The bar for the owner currently filtered to is
marked, which gives the panel a second job: it says which owner you are reading
without the reader going back to the control.
