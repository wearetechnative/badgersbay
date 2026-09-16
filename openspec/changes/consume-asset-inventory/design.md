## Decision: the inventory is a summary, not a report

`asset-inventory.json` describes what the reports say. Treating it as a report
type would make it count toward completeness, and an older client that does not
send it would become incomplete for a reason its owner cannot act on - the same
trap Windows assets fell into before they were reported as `manual`.

So it is extracted and stored like a report, and excluded from the requirement
set. `evaluate_completeness` keeps asking for `sysinfo` and `hardening`, and
nothing else.

## Decision: findings are written into the record, and so is the document

The findings go into `submission.json` beside `asset_id`, `owner` and `class`,
for the same reason those are there: the register moves, the client moves, and
a closed round has to keep reporting what was true when it was scanned.

The whole document is kept as well, under `raw`. The client runs ahead of the
server and will keep doing so - it already emits fields this change does not
model, and it will emit more. Storing only what is modelled today would throw
away the rest at the door, which is the mistake this whole line of work exists
to correct.

## Decision: an unknown schema version is kept, not refused

`schema_version` tells generations apart. A version the server does not
recognise is stored whole and rendered for the fields it does understand.

Refusing would be worse than useless: the submission is evidence regardless of
whether the server can render every field, and a client upgrade would otherwise
take the fleet out of the dashboard until the server caught up.

## Decision: absent is blank, not red

Older clients, and Windows until `honeybadger-k80g` lands, send no inventory.
Their columns read as unknown rather than as a failure. The asset did nothing
wrong, and colouring it red teaches people to ignore the colour.

This is the same distinction the serial handling makes: "not determined" is a
state to report, not an error to raise.

## Decision: value and finding both travel

The client sends both, because "Yes" and "Yes (LUKS)" answer different
questions:

    "disk_encryption": { "value": "Yes", "finding": "Yes (LUKS)" }

The table shows the value; the finding is available on the row, so an auditor
asking "how do you know" can be answered without opening the archive. A value
the client declined to assert arrives as `null` with the finding populated, and
renders as unknown with the reason rather than as a blank.

## What this does not decide

Whether a hardening score of 62 is acceptable. The client already reports its
own verdict in the finding text, and the ISO process owns the threshold. The
dashboard shows the number and the client's finding, and does not add a
judgement of its own.

Colouring a value red or green would be exactly that judgement, so the table
stays neutral: it reports what was found, and leaves what it means to the
process that owns it.
