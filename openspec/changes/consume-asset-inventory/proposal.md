## Why

The client determines every value the ISO register needs and ships them in
`asset-inventory.json`. The server stores the file inside the archive and reads
nothing from it, so an operator still retypes disk encryption, screen lock,
firewall, hardening score and OS currency into the spreadsheet by hand.

That was the point of the whole exercise, and it is the one part that never got
written down. Three proposals deferred it - `asset-register-identity` as a
non-goal, `emit-asset-inventory-json` as "badgersbay does not read this file
yet", and the dashboard mockup as a column group marked "phase 2". Each pointed
at the next, and the last pointed nowhere.

There is also a live consequence. `asset-inventory.json` is a JSON member, so it
reaches `detect_report_type_from_filename()`, which does not know it:

    fastfetch.json          -> fastfetch
    lynis-report.json       -> lynis
    asset-inventory.json    -> None      unrecognised -> HTTP 207

Every submission from a current client now answers 207 with an unrecognised
member. Nothing breaks - the archive is stored and the reports are processed -
but every submission reports that something needs attention when nothing does.

## What Changes

- **Recognise `asset-inventory.json`** as a summary rather than a report, so it
  stops being reported as unrecognised.
- **Read its findings into the submission record**, alongside `asset_id` and
  `owner`, and keep the whole document as well.
- **Show the compliance columns in the fleet view**: disk encryption, screen
  lock, firewall, hardening score, OS up-to-date - the columns the mockup
  marked as phase 2.
- **Show a finding's provenance**, so a value can be traced to what produced it
  without opening the archive.

## Capabilities

### Modified Capabilities
- `tar-submission`: the inventory is extracted, and is not a report type
- `report-storage`: the submission record carries the findings
- `compliance-dashboard`: the fleet view shows them

## Impact

- Submissions from a current client answer 200 again rather than 207.
- Submissions already on disk are not re-read. Their columns stay empty until
  the asset submits again, which is the same rule every other change here
  follows.
- No change to what the client collects or how completeness is judged.

## Non-goals

- Writing the spreadsheet. The register stays the operator's document; this
  fills the dashboard so the values can be read off rather than reconstructed.
- Judging compliance from the findings. Whether a hardening score of 62 is
  acceptable is a threshold that lives in the ISO process, not here.
