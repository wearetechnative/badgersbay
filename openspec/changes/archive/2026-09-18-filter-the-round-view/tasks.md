# Tasks

## 1. Reading the filter

- [x] 1.1 A pure function turning the query string into the four terms, with
      blank and unusable values absent and an unrecognised state dropped
- [x] 1.2 A pure matcher for owner, class and text, folding separators away so
      a hyphenated serial and a bare one find the same asset
- [x] 1.3 A pure function building the round view's address under a filter
- [x] 1.4 Doctests for all three

## 2. Narrowing the table

- [x] 2.1 A pure function returning a narrowed copy of the round state, with
      the round's own figures carried through untouched
- [x] 2.2 The narrowed copy reports what is shown, what is hidden, and which
      terms are active
- [x] 2.3 `_round_table()` renders from the narrowed copy and nothing else does

## 3. The controls

- [x] 3.1 A GET form above the table offering state, owner, class and a search
- [x] 3.2 Owner and class options come from the assets actually in the round
- [x] 3.3 The per-owner bars link to that owner's view and mark the active one
- [x] 3.4 The round selector carries the filter, so `period=` and the filter
      compose

## 4. Saying what is hidden

- [x] 4.1 A notice naming the active terms and the number hidden, with a link
      back to the whole round
- [x] 4.2 The notice appears even when the filter hides nothing
- [x] 4.3 An empty table under a filter says so rather than reading as an empty
      round
- [x] 4.4 An unrecognised state is reported rather than silently honoured

## 5. Verify

- [x] 5.1 The summary block is byte-identical under every filter in turn
- [x] 5.2 Each term narrows the table as specified, and they compose
- [x] 5.3 A serial found with and without its separators
- [x] 5.4 A filtered link to a closed round works
- [x] 5.5 Doctests and `python3 -m unittest test_asset_inventory`
- [x] 5.6 `openspec validate --strict`
