---
description: Light check of a change — its scenarios against its tests, then correctness against the project's rules; no timings
user_invocable: true
argument: Optional — a brief or spec folder to judge against, a git range (default main...HEAD plus the working tree), or "all" for a whole-suite coverage audit
---

# Review

The check every change gets: each step of a feature, or any change made ad hoc. It reads the
diff, not the whole project, and runs no benchmarks or paid calls: the heavy checks are
`/validate`'s, once per feature.

## Input
- **The change:** `git diff main...HEAD` plus the working tree and the untracked files in
  `git status` (not editor folders such as `.idea/`), or the range given.
- **What to judge against:** the brief or spec folder given, else the spec folders whose files
  the diff touches. Both CLAUDE.md files apply; the project's is more specific. Its "Workflow"
  section names the gate and the review checklist.

## Pass 1: scenarios against tests
For each scenario the diff adds or changes (in `specs/**/*.feature`), and each scenario the
brief promises:
- a test cites it the way the project's conventions say (find it by the citation, don't read
  every test file);
- the test asserts what each Then clause says, with the scenario's values, not only a shape;
- the test is at the scenario's level (a gateway scenario has a gateway test);
- ambient state the scenario names is set explicitly (`/design` § 5).

Also: a renamed or removed scenario leaves no dangling citation (tests, design docs, ADRs), and
a test the diff adds that cites nothing either belongs to a scenario that is missing or is an
implementation-level test.

## Pass 2: correctness
Run `/code-review` on the change at effort `high`. Then check, whether or not it raised them:
- **Layers:** dependencies point one way; persistence stays in its layer.
- **Transactions:** the service owns them; no slow or external call inside one; nothing partial
  is written when a step fails.
- **Gateways:** they represent and decide no domain outcome; shared wording is not copied.
- **The project's review checklist**, item by item.
- **Reuse:** where a rule existed, it was reused, not copied.
- **The conventions:** values built whole, validation by the three-question rule, data access as
  if remote and concurrent (`/design` §§ 2–4), tests of public behavior.
- **The deterministic guards** the gate holds (statement and call budgets, query plans,
  idempotency, fault injection) cover any new write, read or external call, each with a case
  that runs the new path at the sizes its guard compares. Timings are not this skill's: a hot
  path goes to `/validate`.
- **No check loosened:** the diff of the project's guard files (linter, type-checker and
  import-rule config, guard tests and their exemption lists, the test fences), and every added
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
2. Pass 1: gaps and weak tests, each with the scenario name and test file:line. Or "none".
3. Bugs, most severe first: severity, file:line, the defect in one sentence; the failure (inputs
   or state → wrong outcome); verified or by reading; the fix in one line.
4. Nits, one line each.
5. Candidate guards: a finding a linter rule or a guard test could have caught, with the rule or
   check that would catch it next time. Or "none".
6. One line per area checked and found clean.

## `all`: whole-suite audit
Every scenario in `specs/` against the tests: a table (spec, scenario, test, Covered / Missing /
Documented-only), weak tests, orphan tests, stale citations in docs, and `@documented-only`
scenarios that may now be automatable. Route missing scenarios to `/bdd`, missing tests to
`/tdd`, test smells to `/refactoring`.
