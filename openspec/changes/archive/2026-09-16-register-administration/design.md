## Decision: an exception is not a pass

Marking an excepted asset as green would fold two different facts into one
colour: "we hold evidence" and "we hold an excuse". An auditor separates those
first, and the ISO tool needs the deviation count as a number rather than as
something to reconstruct.

    wrong           10 / 11 OK

    right           8 scanned - 2 excepted - 1 outstanding
                    ############------

The round is closeable at `outstanding = 0`, which is the behaviour asked for.
The categories stay distinct in the display and in the stored record.

## Decision: exceptions are keyed per round

An exception is `(asset_id, audit_period)`. An asset unreachable in September
may be perfectly reachable in March, and an exception that outlived its round
would quietly suppress a real gap. Keying per round makes expiry automatic:
when the next round opens, nothing carries over and nothing needs clearing.

    reports/exceptions/2026-09/TARI-00031.json
      { "asset_id": "TARI-00031", "audit_period": "2026-09",
        "reason": "Laptop in repair; replacement not yet rolled out",
        "marked_by": "wtoorren", "marked_at": "2026-09-16T09:12:03+02:00" }

On disk, next to the reports, for the same reason the reports are: it is
evidence, it survives an index rebuild, and it can be handed to an auditor.

A reason is required. An exception without one is indistinguishable from a
mistake, and it is the reason that the ISO tool's justification points back to.

## Decision: a submission beats an exception

If an excepted asset submits after all, the submission counts and the exception
lapses without ceremony. The alternative — requiring the operator to withdraw
it — creates a state where evidence exists but is not counted, which is worse
than any bookkeeping it saves.

## Attribution is self-reported

The dashboard is protected by one shared password. `marked_by` is therefore a
free-text field the operator fills in, not an authenticated identity. This is
acceptable for a single-operator tool but must not be dressed up: the field is
labelled as self-reported wherever it is shown.

## Decision: the register is delivered as an agenix secret

Badgersbay is deployed through badgersbay -> elastinix (NixOS module) ->
tn_workloads (IaC). The module already carries two agenix-delivered file
options, `tokenFile` and `dashboardPasswordFile`; `assetRegisterFile` is the
third of the same shape.

Dashboard upload was considered and rejected. The register pairs employee names
with hardware serials, and delivered through IaC it is encrypted at rest with
every change reviewed and dated in git — the strongest form of audit trail this
system can offer, and the same track the other two sensitive files already use.
The cadence suits it: the register changes when scope changes, and scope changes
are exactly the events that deserve a reviewed commit.

This keeps the write path narrow. Badgersbay accepts exactly one kind of write
from the browser — an exception with a reason — and never accepts a change to
the denominator of its own compliance report.

### Consequences for validation

The register arrives as a file at service start rather than through an
interactive form, so there is no moment at which to ask for confirmation.

- **Structurally invalid** — duplicate active serial, unknown class, overlapping
  validity for one serial — the service refuses to start. Failing loudly at
  deploy time is right: a broken register is a broken compliance report.
- **Structurally valid but smaller** — the service starts and reports the
  disappearance prominently, listing which assets are gone. A filtered or
  truncated export silently raises the coverage rate, which is the one
  direction a compliance number must never move by accident. Refusing to start
  would be wrong here: a legitimate shrink is normal, and taking the portal down
  mid-round because two laptops were retired is worse than the risk.

The previous register is retained on disk for that comparison, so the
disappearance can be computed across a restart.

## Risks

- **A write path in a read-only tool.** Both controls are same-origin forms
  behind basic auth on internal infrastructure. That is proportionate here and
  should be stated rather than assumed.
- **Exception as the path of least resistance.** Marking is cheaper than
  chasing. The required reason and the separate count are the only guard; if
  the excepted category grows round over round, that is the signal, and the
  fleet view already shows it.
