---
description: Run a TDD cycle — write failing test, implement, green, refactor, lint
user_invocable: true
argument: Description of the behavior to implement
---

# TDD Cycle

You are running a strict TDD workflow. Follow these rules exactly.

## Input

The user provides a description of behavior to implement. If feature files exist in `features/`, check them first — the scenario may already be specified there.

## Process

For each piece of behavior, repeat this cycle:

### 1. Red — Write a Failing Test

- Write the simplest test that captures the next piece of behavior.
- Decide first whether it is a unit or an integration test (see "Unit or integration" below), and put it in that tree.
- Follow the project's existing test patterns (check `tests/` for conventions: test client, fixtures, mocking approach).
- Follow given-when-then structure with blank lines separating sections.
- **Ambient-state seams.** If the test needs deterministic control of a dependency's ambient state (clock, randomness, env, filesystem), prefer a thin subclass that overrides the public seam over module-namespace patching of the dependency. See `/design` § 5.
- Run the test suite and confirm the test **fails for the right reason**.
- If it passes unexpectedly, the test is too weak — tighten assertions.

### 2. Green — Minimum Implementation

- Write the **minimum code** to make the failing test pass. Nothing more.
- No untested code. If no test requires it, don't write it.
- Run the full test suite — confirm **all tests pass**, not just the new one.

### 3. Refactor (only when green)

- Look for: duplicate code, unclear names, mixed abstraction levels, dead code.
- One refactoring at a time. Run tests after each.
- Do NOT change test assertions during refactoring.
- Do NOT add behavior during refactoring — go back to Red for that.

### 4. Lint

- Run the project's lint command after each complete cycle.
- Fix any issues immediately before starting the next cycle.

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

## Test Discovery (ZOMBIES)

Use this to find the next test to write:
- **Z**ero/empty cases
- **O**ne item cases
- **M**any items cases
- **B**oundary transitions
- **I**nterface clarity
- **E**xceptions/errors (happy paths first)
- **S**imple scenarios first

## Output

After each cycle, report:
- Test name and what it covers
- Pass/fail status
- Any refactoring done
- Lint status
- **Design touchpoints** (surface, don't act):
  - **New modules added** — these need entries in the module map (see `/design` § 2). Update the map in the same change.
  - **Non-obvious decisions surfaced** — implementation choices with seriously-considered rejected alternatives, choices that would surprise an unfamiliar reader, or choices that constrain future change are candidates for an ADR (see `/design` § 6). Don't carry them silently in code; raise them for an ADR pass.

After all cycles complete, run the full test suite one final time and report the result.
