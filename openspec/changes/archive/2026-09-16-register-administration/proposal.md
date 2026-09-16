## Why

An asset that cannot be scanned in a round is a deviation, justified in the ISO
tool. Badgersbay does not need to hold that justification, but it does need to
record that one exists — otherwise the round never closes and the outstanding
list stays permanently red, which is the fastest way to teach people to ignore
it.

`asset-register-identity` establishes the register and the round view but loads
the register from a path and says nothing about how an operator maintains
either. This change adds that: marking an asset as excepted for a round, and
delivering the register to a server the operator does not edit files on.

## What Changes

- **Exception marking**: a control on the round view marks an asset as excepted
  for the open round, with a required reason. Stored per `(asset_id,
  audit_period)`, so it expires when the next round opens.
- **Round arithmetic gains a third category.** Progress reads
  `scanned / excepted / outstanding`, not `OK / not OK`. A round is closeable at
  `outstanding = 0`; the deviation count stays legible because the ISO tool
  needs it as a number.
- **A submission always beats an exception.** If an excepted asset submits
  after all, the submission counts and the exception lapses.
- **Register delivery** is an agenix secret, delivered through the elastinix
  module as `assetRegisterFile`, alongside the existing `tokenFile` and
  `dashboardPasswordFile`. Dashboard upload is explicitly not built: badgersbay
  accepts an exception from the browser and never a change to the denominator
  of its own compliance report.

## Capabilities

### Modified Capabilities
- `asset-register`: exception records, register delivery and replacement
- `compliance-dashboard`: exception control, three-category progress

## Impact

- **Badgersbay becomes writable from the browser.** Until now it only accepted
  uploads from authenticated clients and served read-only HTML. The dashboard
  is protected by a single shared password, so `marked_by` is self-reported and
  must not be presented as authenticated attribution.
- **Exceptions are evidence.** They are stored on disk alongside reports, so
  they survive an index rebuild and are reviewable by an auditor.
- **Prerequisite**: `asset-register-identity`.
- **Requires** elastinix `elastinix-l16a` for the `assetRegisterFile` option.

## Non-goals

- Holding the justification itself. The ISO tool is where a deviation is
  argued; badgersbay records that one was recorded, by whom and when.
- Approval workflow. One operator, no second signature.
