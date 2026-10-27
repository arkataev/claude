---
description: Build behavior test-first — red, green, refactor — one scenario at a time, gate at the end
user_invocable: true
argument: The scenarios or behavior to implement (a spec folder, a brief, or a description)
---

# TDD

You are building behavior test-first. Follow these rules exactly.

## Input

The scenarios come from the feature's spec (`specs/<feature>/*.feature`, and the "Affected specs"
its `spec.md` lists) or a brief that names them. With no spec, ask whether one should be written
first (`/bdd`); a one-off fix may go without.

## The cycle (per behavior)

### 1. Red
- Write the simplest test that captures the next piece of behavior (ZOMBIES below).
- Test at the level the scenario describes: a screen, bot or API scenario gets a gateway test,
  not only a service test.
- Decide unit or integration first (below), and put it in that tree.
- Follow the project's test conventions (naming, citing the scenario, fixtures) and
  given-when-then with blank lines between the sections.
- **Ambient state** (clock, randomness, env, filesystem): a thin subclass over the public seam,
  never module-namespace patching (`/design` § 5).
- Run that test alone and see it **fail for the right reason**.

### 2. Green
- The **minimum code** that passes it. No untested code.
- Re-run the affected test files.

### 3. Refactor (only when green)
- Duplicate code, unclear names, mixed abstraction levels, dead code; one change at a time.
- Never change a test's assertions, never add behavior (back to Red for that).

### A test that passes at once
It proves nothing until it fails. Break the code on purpose, see the test fail, restore it. In
Python run these checks with `PYTHONDONTWRITEBYTECODE=1`: a restored file of the same size within
the same second can keep the mutant's stale `.pyc`. Count these tests in the report.

### Cadence
- Each cycle: the new test, then the affected files.
- After each section of the work (a brief's numbered change, a group of scenarios): the full
  test suite.
- At the end: the project's gate (lint, types, tests). Fix what it finds before reporting.

## Unit or integration

Two kinds of test, kept in two trees (`tests/unit/`, `tests/integration/`, each mirroring the source tree) so the kind shows in the path and the unit suite runs alone, fast, with no infrastructure.

**Unit test** — business logic, nothing else.
- Opens no database (an in-memory one is still a database), file, socket, subprocess or real model; reads no real clock or environment. The unit tree's conftest makes those fail, so a slip is caught, not trusted.
- What the code under test calls across a boundary — repositories, ports, the application API, I/O callables — is an autospec mock (`create_autospec(Repo, instance=True)`), never a hand-written fake of the adapter: a fake re-implements the adapter's behavior and drifts from it. A unit of work's `run(work)` mock just calls `work`.
- Arrange the mocks' return values as the facts the logic decides on (domain values, not rows). Assert on what comes back and on the **writes** handed to the mocks (a write is the code's output); never assert on which reads happened or in what order. A test that has to script many reads is pointing at logic that belongs in a domain value: move the rule there and test it directly.
- Layers: domain rules (no mocks at all), services (repositories and ports mocked), gateways (the application API mocked; assert on what is rendered or sent).

**Integration test** — an adapter against its real dependency.
- Repositories against the real engine (SQL, constraints, triggers, migrations, locking), parsers against real files, HTTP clients against a fake server, the wiring end to end.
- One end-to-end path per use case through the real wiring proves the parts fit; it does not re-test each rule (the unit tests do).
- Guards that read the source tree (static checks) live here too.

**Choosing.** A rule is tested at unit level; the SQL, serialization or protocol that carries it at integration level. Never test a business rule only through the database. Most tests are unit tests: if the integration tree outgrows the unit tree, rules are being tested in the wrong place.

## Test discovery (ZOMBIES)
**Z**ero, **O**ne, **M**any, **B**oundaries, **I**nterface, **E**xceptions (happy paths first),
**S**imple scenarios first.

## Report (once, at the end)
- Tests added, by scenario; the test count before and after.
- Tests that passed at once and were checked by breaking the code.
- The gate result.
- **Design touchpoints** (surface, don't act): new modules (the module map, `/design` § 2);
  non-obvious choices that may need an ADR (`/design` § 6); a scenario that turned out wrong or
  missing (back to the spec, `/bdd`).
