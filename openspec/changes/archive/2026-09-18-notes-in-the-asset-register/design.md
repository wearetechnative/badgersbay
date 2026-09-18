# Design

## Filtering before the parser, not inside it

`csv` has no comment character and no hook to add one. The filter therefore sits
in front of the reader: `register_lines()` takes the open file and yields the
lines that are not notes, and `csv.DictReader` is handed that generator instead
of the handle. `DictReader` accepts any iterable of strings, so nothing else
about the loader changes - quoting, embedded commas and the `utf-8-sig` BOM are
still the `csv` module's job, which is where they belong. The example register's
`"MacBook Pro 14"", M3, 2024, 18Gb"` keeps working because no code in this change
looks at a field.

A line is a note when its first non-whitespace character is `#`. Leading
whitespace is allowed so a note can be indented under the row it explains. The
test that this costs nothing is that no value the register holds can start with
`#`: `asset_id` is `TARI-` plus digits, `serial` is normalised by
`normalise_serial()` to a single uppercase token from hardware, `class` and
`status` are closed vocabularies, and the three dates are `YYYY-MM-DD`. Only
`owner`, `model` and `departure_reason` are free text, and none of them is a
first column.

## The numbers in errors are line numbers, and stay that way

`_parse_row()` reports `assets.csv row 7: ...`. Before this change that number
came from `enumerate(reader, start=2)`, which is the file's line number only
because the header was line 1 and every row followed it one per line. Filter
notes out and that arithmetic silently starts pointing at the wrong line - and
since every note shifts it by one, the error would drift further into the file
the more of them somebody wrote. A register that punishes commenting by
mislabelling its own errors would be worse than one that refuses them outright.

So `register_lines()` yields `(line_number, text)` and the loader keeps the
numbers alongside the text it feeds the reader. `reader.line_num` counts the
lines the reader has consumed - filtered lines, not file lines - which is exactly
the index needed back into that list. The number in an error is therefore the
line the maintainer opens the file to, notes included.

This also fixes something that was already wrong: a blank line or a field with an
embedded newline used to offset every message after it. Those are rarer than a
comment will be, and neither was worth a change on its own.

## Saying what was read as the header

The bean asks for the error to name the first line instead of listing the columns
that were expected. Both are worth having: the columns say what was wanted, the
line says what arrived, and the gap between them is the diagnosis. The message
becomes

    assets.csv line 4 is not a usable header: missing required column(s):
    asset_id, class, owner, serial. The line reads: 'TARI-00023;PF50L2MR;...'

The line is quoted with `repr()` so a stray BOM, a trailing space or a tab is
visible rather than invisible.

The shape of the failure does not change: `AssetRegisterError`, raised from
`load()`, refusing startup. A register whose header cannot be read is a register
whose rows cannot be trusted, and the decision that a compliance figure built on
an untrustworthy register is worse than no figure was made when the loader was
written.

An empty file gets its own message rather than the missing-column list, because
"missing every column" is a confusing way to say "there is nothing here". A file
holding only notes is empty by the same measure and reads the same way.

## Comments are dropped, not kept

The server never writes the register. It is delivered as an agenix secret and is
read-only to the service, so there is no round trip in which a comment could be
lost - and adding comment preservation would mean adding a writer first.

Nor is anything parsed out of a comment. Once a `#` line can carry meaning,
somebody writes `# exception: TARI-00031 2026-09 awaiting client` and it is
silently ignored, which is the failure mode this change exists to remove. A note
is prose for a person. Exceptions already have a store, departures already have a
column, and a fact the service acts on belongs where it is validated.
