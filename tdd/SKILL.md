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
