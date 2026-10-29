---
description: Code no test can miss — the checklist that leaves a mutation sweep nothing to find, at write time and in review, and how to sort a sweep's survivors
user_invocable: true
argument: Optional — the files or git range to check by reading (default the working-tree diff)
---

# Mutants

A mutant is one small change to the code: `<` becomes `<=`, a call is deleted, a text is emptied.
It survives when no test fails. A survivor is a weak test or dead code. A mutation sweep finds
survivors after the fact and is slow (minutes per file); this checklist is what keeps it from
finding any. The writer applies it while writing (with `/tdd`), the reviewer in `/review` Pass 1,
and an audit when it sorts the sweep's survivors. Judge only the lines a change adds or edits.

## Every line a test can see
For each such line, some test fails when:
- **a comparison moves** (`<` ↔ `<=`, `==` ↔ `!=`, `in` ↔ `not in`, `is` ↔ `is not`): a case at
  the boundary value itself, not only on either side of it;
- **a condition loses an operand** (`and` ↔ `or`, a `not` dropped): for each operand, a case
  where it alone decides;
- **a constant changes** (a text emptied, a number moved by one, `True` ↔ `False`): constant
  text the user sees is asserted whole, prompts, separators and punctuation included; a limit or
  size has a case at it; a flag has a case for each value;
- **a call statement or an `if`/`else` body is emptied**: a test sees its effect. A call nothing
  can see (a reset of what is already empty) is not written;
- **a `return` gives `None` or empty** (`[]`, `{}`, `()`, `set()`, `''`): a test asserts what
  came back, not only that something did;
- **an argument is dropped or passed as `None`**: a test where its value changes the result. An
  argument no path reads goes, with its parameter;
- **a normalizing or wrapping call is removed** (`strip`, `lower`, `casefold`, `.copy()`,
  `list(...)`, `tuple(...)`, `dict(...)`): an input that needs it (padded or mixed-case text);
  for a defensive copy on a frozen value, a test that changes the source after the value is
  built and sees the value unchanged;
- **a SQL clause changes** (`ORDER BY` and its direction, `DISTINCT`, `LEFT JOIN`,
  `COLLATE NOCASE`, `IS NULL`, `MIN`/`MAX`, `AND`/`OR`, `NOT`, `<`/`>` ↔ `<=`/`>=`): the test's
  rows need it: two rows out of order, a duplicate the result would show, a row with no match, a
  case variant, a NULL, a value at the bound. `OR IGNORE` becomes `OR REPLACE`: a conflicting row
  whose other columns differ, not an identical one. A clause no caller's result depends on is not
  written;
- **a default is used**: a default is written only when a caller relies on it, and that caller has
  a test.

## What no test should see
- Developer-facing text: an exception's message no gateway shows, log wording.
- Type-only code: `cast`, `assert_never`, a functional `TypedDict`.
- An enum's value compared only by member.
- Code a linter, the type checker or a project invariant requires, whose change no input reaches:
  `zip(strict=True)` over sequences of one length, `markup=False` on constant text, `dict(row)`
  handed to `from_row`, `[0]` of a one-element row.

A test of these pins nothing; they belong in the project's list of equivalent mutants. Anything
else no test sees is a test to write or code to delete.

## Checking one suspect
- **The writer** checks in place, as `/tdd` "A test that passes at once" says: make the one
  change, run the tests that reach the line with `PYTHONDONTWRITEBYTECODE=1`, restore.
- **The reviewer**, read-only, checks in a throwaway copy: copy what the sweep's settings copy
  (not the database or the virtual environment) and run the project's interpreter with the
  copy's source first on `PYTHONPATH`. An editable install otherwise imports the working tree,
  and every mutant "survives".
- No failure: it survives. Neither runs the sweep; it runs in an audit.

## Sorting survivors
Each survivor is one of:
- **a weak test:** write the test that fails on it (`/tdd`, Red);
- **dead code:** nothing could see it, so delete it;
- **an equivalent:** no input tells it apart. It goes in the project's list with a reason that
  holds for its line: the list's existing reason, word for word, where one fits.

The list is an exemption list, like a linter's ignore list. An entry is added only where the
brief or the user allows it, and one that hides a weak test is a bug. The writer never changes
the list; an entry the sweep reports stale (its code is gone, or a test now kills it) is removed
in the audit.

## The audit
The sweep is an audit of the whole tree, not a step of each feature. A survivor depends on every
test, so a sweep of one feature's files misses what other changes weaken, and a whole-tree sweep
takes too long to run per feature. It runs when the user asks (suggest one after a few features
have merged), on a branch `audit/mutation-<date>`, with the project's mutation command over every
source file, in the background:
1. sort every survivor the list does not explain (above), and remove the stale entries;
2. confirm the sort by hand ("Checking one suspect") or with a sweep of the files involved, never
   by running the whole audit again;
3. the gate passes; one changelog entry with the audit's numbers (mutants, kills, survivors,
   time), and the roadmap's audit item names this one; merge `--no-ff`.

## Report (when invoked alone)
Per suspect: file:line, the change no test notices, and how it was checked (by hand or by
reading); then what it is (weak test, dead code, equivalent with its reason).
"Nothing found" is a valid answer.
