# Design

## The selector is a form, not a script

The obvious implementation is a `<select>` with an `onchange` handler. The
dashboard these views replaced did exactly that, and its filter needed fixing
twice.

This is a plain `<form method="get">` with a select and a submit button. It
works with scripting disabled, it produces a URL that can be reloaded and
pasted, and it can be tested by parsing HTML rather than by driving a browser.
The cost is one small button; the benefit is that the control cannot silently
stop working.

The active tab travels as a hidden field, so changing the round keeps you on the
view you were reading.

## Which rounds are offered

The rounds that have submissions, plus the current one.

The second half matters more than it looks. The list of rounds with data is
derived from the submissions, so a round nobody has submitted to yet does not
appear in it - and that is precisely the round you are looking at when a round
opens. Without the addition, the round you are viewing would vanish from its own
selector at the moment it is emptiest.

Newest first, because the current round is what people come for.

## A round with no submissions is an answer

An empty round is not an error. The register still says who was expected, so the
view can report that nobody scanned - which is a finding rather than a failure.
This needs no special case; it falls out of computing the buckets from the
register and an empty submission set, and the tests pin it so it stays that way.

## Scoping a closed round was already right

`in_scope(window_start, window_end)` selects rows whose validity window overlaps
the round's window, so asking for a past round returns the assets that were in
scope then, not the ones in the register now. A device issued in August is
absent from the March round and present in September, and an asset retired since
is still counted in the round it belonged to.

This is the property that makes a historical compliance figure stable, so it is
covered by a test in this change even though no code changed for it. A
regression here would rewrite the past quietly.
