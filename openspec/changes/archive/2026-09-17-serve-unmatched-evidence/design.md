# Design

## Whether to serve it at all

The bean left this open, and it is the only question here worth weighing.

An unmatched submission is evidence from a machine nobody has tied to an asset,
and the dashboard is behind one shared password. That is the argument for
leaving it unreachable.

It does not survive contact with what the dashboard already does. Every
registered asset's archive is already one click away behind that same password -
the same tar, the same reports, from machines the register happens to name. An
unmatched record is not more sensitive than a matched one; it is less
identified. Withholding it protects nothing and costs the round view its
purpose: an alert nobody can act on teaches people to stop reading alerts.

So it is served. The state that existed until now was not a judgement about
sensitivity - it was the shape the route happened to have when it was written
for one tree.

## The tree is in the path, not guessed from it

The two trees are keyed differently. `submissions/` is keyed on the hardware
serial; `unmatched/` on `hostname-username`. Nothing forbids a serial from
looking like a hostname-username pair, so resolving a key against both trees in
turn would mean a record shadowing another for no reason a reader could see.

The tree is therefore a segment of its own:

    /evidence/unmatched/lobos-wtoorren/2026-09-17T09-00-00/lynis-report.json

and it is checked against an allowlist of the trees the server writes, never
used as a path component in its own right. `2026-03/` is history the server only
reads, and it is not on the list.

The three-segment form stays valid and means `submissions/`. Every link the
dashboard has emitted so far has that shape, and a URL somebody filed in a
compliance sheet should not stop working because the route learned a second
tree.

## A link comes from where the record was written

The round table built its hrefs from `entry['serial']` - the register's value
for the asset the record resolved to. An unmatched record has no entry, which is
why it had no link.

`record_dir` is the honest source: it is where the file actually is, for both
trees, and its last two segments are exactly the key and the record stamp the
route needs. Using it also removes a latent mismatch in the matched case, where
the register's serial and the serial the client sent need not be spelled
identically.

A record the route does not serve - the period archive - yields no href, and the
view shows what it holds as text rather than as a broken link. That is the same
rule the badges already followed for a report with no known filename.
