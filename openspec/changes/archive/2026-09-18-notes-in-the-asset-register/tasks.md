# Tasks

## 1. Reading past the notes

- [x] 1.1 A pure function numbering the register's lines and dropping the ones
      whose first non-whitespace character is `#`
- [x] 1.2 `load()` feeds the reader that generator instead of the file handle
- [x] 1.3 Row numbers in errors are the line numbers of the file, notes counted
- [x] 1.4 Doctests for the function, including a note above the header, a note
      between rows and an indented one

## 2. The header error

- [x] 2.1 An unusable header raises `AssetRegisterError` naming the line number
      and quoting the line, alongside the columns that were expected
- [x] 2.2 A file that is empty once the notes are skipped says so, rather than
      listing every column as missing

## 3. Saying so where the format is documented

- [x] 3.1 `assets.csv.example` carries the notes it was written to have: the
      serial that disagrees with the ISO tool, the two rows of one asset across
      a mainboard replacement, the departure with a reason, and the class that
      sits outside the denominator
- [x] 3.2 The README's register section states that `#` lines are notes

## 4. Verify

- [x] 4.1 A register with a leading comment loads, and its rows are the rows
- [x] 4.2 A comment between rows is skipped and does not become a row
- [x] 4.3 A row error in a commented register names the line in the file
- [x] 4.4 The header error quotes the offending line
- [x] 4.5 Mutation-check 4.1: remove the skip, confirm the test fails
- [x] 4.6 `python3 -m doctest honeybadger_server.py` and
      `python3 -m unittest test_asset_inventory`
- [x] 4.7 `openspec validate --strict` and `openspec validate --specs --strict`
