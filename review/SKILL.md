---
description: Review feature scenarios against tests — find gaps in coverage
user_invocable: true
argument: Optional specific feature file or area to review (default: all features)
---

# Coverage Review

Compare feature file scenarios to existing tests and identify gaps.

## Process

### 1. Read Feature Files

Read all `.feature` files in `features/` (or the specific one requested). Extract every scenario with its tag.

### 2. Read Test Files

Read all test files in `tests/`. Map each test function to the behavior it covers.

### 3. Build Coverage Table

For each scenario, find the corresponding test(s):

| Feature | Scenario | Tag | Test | Status |
|---------|----------|-----|------|--------|
| Name | Scenario name | @tag | `test_file::test_name` or "—" | Covered / Missing / Documented-only |

Rules:
- `@documented-only` scenarios → status is "Documented-only" (expected, not a gap)
- Scenarios with a matching test → "Covered"
- Scenarios without a matching test and no `@documented-only` tag → "Missing" (this is a gap)

### 4. Assess Test Quality

For covered scenarios, check if the test actually validates what the scenario describes:
- Does the test assert on the specific values mentioned in the scenario (not just response shape)?
- Does the test cover the full scenario (all Then/And clauses), or just part of it?
- Does the test control ambient state explicitly when the scenario specifies it (clock, randomness, env, filesystem)? Tests that leave ambient state uncontrolled are flaky; tests that reach for module-namespace patching where a thin-subclass seam exists are fragile (see `/design` § 5 and `/refactoring`'s smell catalog).
- Flag weak tests that pass for the wrong reason.

### 5. Check for Orphan Tests and Stale Citations

**Orphan tests.** Find tests that don't map to any scenario. These might indicate:
- Missing scenarios (feature file needs updating)
- Implementation-level tests that don't need a scenario (repository, internal logic)
- Dead tests that should be removed

**Stale citations.** Scan design docs / ADRs / READMEs for references to feature scenarios (e.g., `features/X.feature` § "scenario Y") and verify each one still resolves to a current scenario. Renamed or removed scenarios leave dangling citations in the docs — flag them. This complements the orphan-tests check on the *documentation* side of the scenario surface.

### 6. Recommend Next Steps

Based on gaps found:
- Missing scenarios → suggest writing them (offer to run `/bdd`)
- Missing tests → suggest implementing them (offer to run `/tdd`)
- Weak tests → suggest tightening assertions
- Ambient-state mismanagement (uncontrolled or namespace-patched) → route to `/refactoring` (its smell catalog has the tactic)
- Stale doc citations → update in place during the next structural pass (citation hygiene per `/design` § 6); route to `/refactoring` if a refactor is already underway
- Stale `@documented-only` → check if they're now automatable

## Output

1. Coverage table
2. Summary: X covered, Y missing, Z documented-only
3. Orphan tests (if any)
4. Stale doc citations (if any) — scenario references in docs/ADRs that no longer resolve
5. Recommended actions
