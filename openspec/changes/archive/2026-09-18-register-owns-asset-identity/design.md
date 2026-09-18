# Design

## Removed and added, not modified

The temptation is a MODIFIED block: the requirement keeps its name, the body
turns around, the diff is small. It is the wrong shape here for two reasons.

A requirement's name is part of what it says. "Where the durable identity comes
from", answered with "somewhere else", was the rule for one round of this
register and it was wrong at the time it was written. Rewriting the body under
the same heading leaves no trace that the rule reversed; a reader of the spec
history sees an edit where there was a decision.

The validator agrees, for its own reason. A MODIFIED block must carry the
requirement whole, and the old one holds a scenario - "The register is not the
registrar" - that has no successor. Dropping it inside a MODIFIED block is
exactly what `--strict` objects to. Removing the requirement and adding its
replacement says what happened and passes.

## What the new requirement can honestly claim

Three things are true of the register as a document: a number is assigned here,
a number is never reused, and two rows share an `asset_id` only when they are
the same asset at different times.

None of the three is enforced by the loader. `AssetRegister.load()` validates
the columns it needs, a usable serial, `class` against `VALID_ASSET_CLASSES`,
`status` against `VALID_ASSET_STATUSES`, dates that parse and do not run
backwards, and - in `_check_serial_overlaps()` - that a serial is never valid
for two rows at once. `asset_id` is checked for emptiness and nothing else. A
reused number, or two unrelated assets carrying the same one, loads without
complaint.

So the requirement says so. A scenario states plainly that the discipline is
kept by whoever maintains the register and not by the service, which leaves the
option of enforcing it later as a visible gap rather than a surprise. Writing
the rule without that line would have the spec assert a check that does not
exist, which is the same fault this change is correcting, one layer down.

## Divergence is no longer a defect

Under the old rule, any difference between the tool and the register was a fault
in the register, and `badgersbay-kgl2` carried a list of such faults to be
reconciled. Under the decision there is nothing to reconcile: the export was
read once. The new requirement says that where the two disagree, or where the
tool has no number at all, the register's value stands.

This is worth stating rather than leaving implied, because the old framing
produced real work - hand-assigned numbers logged as discrepancies to be fixed
elsewhere - and nobody should reopen it on reading the spec.

## The serial rule is untouched

"The serial is what the machine reports" stays exactly as it is. It is about a
different column and a different reason: a serial is the key an incoming
submission is matched on, so it has to be the value the machine emits, whatever
any tool holds. That constraint comes from the matching, not from who owns the
register, and the decision does not touch it.
