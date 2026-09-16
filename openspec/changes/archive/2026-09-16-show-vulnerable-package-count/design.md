# Design

## The value stays null, and that is the point

honeybadger deliberately asserts no value for `vulnerable_packages`. The asset
register contradicts itself about which literal in column J means compliant -
its data validation offers `None`, its Status formula counts `Yes` - so the
client refuses to pick one and explains why in the finding text.

That refusal is information and has to survive here. badgersbay must not supply
the verdict the client declined to give, so the column shows the number and the
client's reason and applies no colour. This is the rule the other inventory
columns already follow: the threshold belongs to the ISO process, not to the
dashboard.

## Why `inventory_cell()` gains a fallback rather than the view gaining a case

`inventory_cell()` is the one place that decides what a finding reads as. A
special case in the fleet view for this one field would put that decision in two
places, and the next finding that measures without judging would need a third.

The fallback is stated generally: when `value` is null but the finding carries a
`count`, the count is what there is to report. The cell is then `known` - there
is a measurement - with the client's text as its reason.

A finding with neither reads as unknown exactly as before.

## Why the schema bump is part of this change

`INVENTORY_SCHEMA_VERSION` is documented as the generation the server was
written against, and drives a log line when a document declares something else.
Schema 2 adds only this count. Bumping without reading it would make the
constant claim something untrue and silence the warning that fields are arriving
which nothing renders - the exact condition the constant exists to report.

Rejecting an unknown generation is still not on the table, and the existing
requirement covering that does not change: the client runs ahead of the server
by design, and refusing would take the fleet out of the dashboard on every
client upgrade.

## What is deliberately not done

No completeness rule changes. `asset-inventory.json` remains a summary of the
reports rather than a report, and never reaches `evaluate_completeness()`. A
client that sends no inventory must not become incomplete for a reason its owner
cannot act on.
