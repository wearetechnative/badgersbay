# Tasks

## 1. Read the count

- [x] 1.1 Extend `inventory_cell()` so a finding whose `value` is null but which
      carries a `count` reports the count, with the client's finding text as its
      reason and `known` true
- [x] 1.2 Leave a finding with neither value nor count reading as unknown
- [x] 1.3 Update the docstring examples to cover both

## 2. Show it

- [x] 2.1 Add `vulnerable_packages` to `INVENTORY_COLUMNS` with a column label
- [x] 2.2 Confirm the fleet view applies no colour to it, as for every other
      inventory column

## 3. Declare the generation

- [x] 3.1 Move `INVENTORY_SCHEMA_VERSION` from 1 to 2
- [x] 3.2 Confirm a document declaring an unrecognised generation is still
      stored and rendered rather than refused

## 4. Verify

- [x] 4.1 `python3 -m doctest honeybadger_server.py`
- [x] 4.2 `python3 -m unittest test_asset_inventory`
- [x] 4.3 Add an end-to-end test asserting a real archive's count reaches the
      fleet view
- [x] 4.4 Add a test that a null value with no count still reads as unknown
- [x] 4.5 `openspec validate --strict`
