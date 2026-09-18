# Tasks

## 1. The list of rounds

- [x] 1.1 A pure function returning the rounds to offer: those with
      submissions, plus the current one, newest first, without duplicates
- [x] 1.2 Doctests covering an empty history, a current round with no
      submissions, and ordering

## 2. The control

- [x] 2.1 Render it in `_dashboard_shell()` so both views get it
- [x] 2.2 Carry the active tab, so changing the round keeps the view
- [x] 2.3 No scripting: a GET form that works on its own

## 3. Verify

- [x] 3.1 Doctests and `python3 -m unittest test_asset_inventory`
- [x] 3.2 The selector appears on both views and marks the current round
- [x] 3.3 Selecting a round reaches it and keeps the tab
- [x] 3.4 A round with no submissions renders rather than erroring
- [x] 3.5 A closed round is scoped to the register as it was then
- [x] 3.6 `openspec validate --strict`
