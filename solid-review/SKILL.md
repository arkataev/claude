---
description: The solid flow's review — a change's scenarios against its tests, then correctness against solid-principles and the project's rules; no timings. Preloaded by solid-reviewer
user_invocable: true
argument: Optional — a brief or spec folder to judge against, a git range (default main...HEAD plus the working tree), or "all" for a whole-suite coverage audit
---

# Solid review

The check every change gets: each step of a feature, or any change made ad hoc. It reads the
diff, not the whole project, and runs no benchmarks or paid calls: the heavy checks are
`/validate`'s, once per feature.

This is `/review` for the solid flow (`/solid-workflow`). It judges against the catalog
`solid-principles` and `/solid-design`. Where they differ from the global `CLAUDE.md`, they
win (`solid-principles`, "Precedence").

## Input
- **The change:** `git diff main...HEAD` plus the working tree and the untracked files in
  `git status` (not editor folders such as `.idea/`), or the range given.
- **What to judge against:** the brief or spec folder given, else the spec folders whose files
  the diff touches. Both CLAUDE.md files apply, as `solid-principles` amends the global one;
  the project's is more specific. Its "Workflow" section names the gate and the review
  checklist.

## Pass 1: scenarios against tests
For each scenario the diff adds or changes (in `specs/**/*.feature`), and each scenario the
brief promises:
- a test cites it the way the project's conventions say (find it by the citation, don't read
  every test file);
- the test asserts what each Then clause says, with the scenario's values, not only a shape;
- the test is at the scenario's level (a gateway scenario has a gateway test), and at its
  layer (`solid-principles` V1). An adapter test of its own, a unit test that opens a file or
  a database, and a composition test that starts a subprocess without the brief naming it are
  each a finding;
- ambient state the scenario names is set explicitly (`/solid-design` § 5);
- every line the diff adds to the source is one a test can see (`/mutants`): a suspect is
  checked as that skill says, and is a weak test or dead code.

Also: a renamed or removed scenario leaves no dangling citation (tests, design docs, ADRs), and
a test the diff adds that cites nothing either belongs to a scenario that is missing or is an
implementation-level test.

## Pass 2: correctness
Run `/code-review` on the change at effort `high`. Then check, whether or not it raised them:
- **Layers:** dependencies point one way; persistence stays in its layer.
- **The import graph** (`solid-principles` D1–D3):
  - The domain imports nothing of the app, and an adapter imports nothing of the app.
  - The service is the only module that sees both the domain and an adapter.
  - An adapter builds no domain value and decides no domain outcome.
  - The domain sees no stored value.
  - Each enum mapping between them is an exhaustive `match`.
- **Transactions:** the service opens the adapter's unit of work; how the unit is atomic is
  the adapter's. No slow or external call inside one; nothing partial is written when a step
  fails.
- **Gateways:** they represent and decide no domain outcome; shared wording is not copied.
- **The project's review checklist**, item by item.
- **Reuse:** where a rule existed, it was reused, not copied.
- **The conventions:** values built whole, validation by the three-question rule, data access as
  if remote and concurrent (`/solid-design` §§ 2–4), tests of public behavior.
- **The catalog:** the Code rules of `solid-principles` that no tool holds, and that the diff
  keeps the shape the brief fixed. A Shape rule the brief settled is not reopened.
- **The deterministic guards** the gate holds (statement and call budgets, query plans,
  idempotency, fault injection) cover any new write, read or external call, each with a case
  that runs the new path at the sizes its guard compares. Timings are not this skill's: a hot
  path goes to `/validate`.
- **Equivalent mutants:** each entry the diff adds to the project's list has a reason that holds
  for its line (`/mutants`, "Sorting survivors"). An entry that hides a weak test is a bug.
- **No check loosened:** the diff of the project's guard files (linter, type-checker and
  import-rule config, guard tests and their exemption lists, the test fences, the list of
  equivalent mutants), and every added
  line with a suppression (`noqa`, `type: ignore`, `pragma: no cover`, `xfail`, `skip`). Each
  that the brief does not name is a bug: the gate passing proves nothing once its check is off.
- **The brief or spec:** what it promises, and whether old behavior survives the change.

## Every finding is verified
Try to make it happen: a failing test selection, or a throwaway script outside the repo (against
an in-memory or temporary copy of any data). Mark it **verified** (how) or **by reading**. Drop
anything you cannot tie to a concrete wrong outcome. Judge against the spec and the rules, not
preference.

## Report (≤60 lines)
1. The gate result (run it unless the caller just did).
2. Pass 1: gaps, weak tests and lines no test sees, each with the scenario name and test
   file:line (or the source file:line and the change no test notices). Or "none".
3. Bugs, most severe first: severity, file:line, the rule ID (`solid-principles` `D2`, … or
   `global: <rule name>`), the defect in one sentence; the failure (inputs or state → wrong
   outcome); verified or by reading; the fix in one line.
4. Nits, one line each.
5. Candidate guards: a finding a linter rule or a guard test could have caught, with the rule or
   check that would catch it next time. Or "none".
6. One line per area checked and found clean.

## `all`: whole-suite audit
Every scenario in `specs/` against the tests: a table (spec, scenario, test, Covered / Missing /
Documented-only), weak tests, orphan tests, stale citations in docs, and `@documented-only`
scenarios that may now be automatable. Route missing scenarios to `/bdd`, missing tests to
`/solid-tdd`, test smells to `/refactoring`.
