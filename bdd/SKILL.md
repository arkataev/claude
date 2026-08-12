---
name: bdd
description: Define feature scenarios and derive tests from them using BDD → TDD workflow
user_invocable: true
argument: Feature or behavior to specify
---

# BDD Feature Specification

You are defining behavioral specifications as Gherkin feature files, then deriving tests from them.

## Input

The user describes a feature, capability, or domain concept. You will:
1. Write the feature file
2. Review existing tests for coverage
3. Identify gaps and implement missing tests via TDD

## Step 1 — Write the Feature File

Create or update a `.feature` file in `features/`:

```gherkin
Feature: Short Descriptive Name
  As a <role>
  I want to <capability>
  So that <business value>

  Background:
    Given <shared preconditions>

  Scenario: One specific behavior
    Given <precondition>
    When <action>
    Then <observable outcome>
```

Rules:
- One feature file per domain concept (not per endpoint or class)
- Scenarios describe **behavior from the user's perspective** — no implementation details
- Use `Background` for preconditions shared by all scenarios
- Use tags for test categories:
  - `@integration` — requires external services
  - `@sequence-mock` — uses mock with sequenced responses
  - `@documented-only` — can't be automated yet (add a comment explaining why)
- Start with happy paths, then error cases, then edge cases
- Include comments for domain rules and non-obvious business logic
- **Explicit ambient state.** When a scenario depends on ambient state (current time, randomness, env, filesystem), the `Given` step must name the value explicitly (e.g., "Given the clock reads 14:00"). Don't leave ambient state implicit — non-deterministic scenarios produce flaky tests. The test layer will set the value via the thin-subclass seam from `/design` § 5.
- **Audience-resolvable language.** Feature files are part of the project's documentation surface — readers of the docs may consult them as authoritative behavior specs. Use terms that resolve in that audience (domain vocabulary defined in the project), not internal jargon or references to private notes.

## Step 2 — Coverage Review

Compare each scenario to existing tests:

| Scenario | Test | Status |
|----------|------|--------|
| Name     | test function or "—" | Covered / Missing / Documented-only |

Present this table to the user.

## Step 3 — Implement Missing Tests

For each missing automatable scenario, run a TDD cycle:
1. Write a failing test that implements the scenario
2. Implement minimum code to pass
3. Refactor when green
4. Run lint

Skip `@documented-only` scenarios — they stay as specifications only.

## Output

Report:
- Feature file created/updated (path)
- Coverage table
- Tests added (names and what they cover)
- Any scenarios left as documented-only and why
- **Design touchpoints** (surface, don't act):
  - **Scenarios added, renamed, or removed** — design docs and ADRs may cite feature scenarios by name (e.g., `features/X.feature` § "scenario Y"). Audit those citations for drift and update them in the same change (citation hygiene per `/design` § 6).
  - **New feature file added** — if the project's design doc enumerates feature files as a spec-surface index, add the new file there.
