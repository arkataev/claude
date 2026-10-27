---
name: bdd
description: Write or update a feature's spec — specs/<feature>/spec.md and its Gherkin scenarios — the first step of every change
user_invocable: true
argument: The feature (a roadmap item) or the behavior change to specify
---

# Spec (BDD)

Every change starts here. A spec says what the feature does and how we will know it does it,
before anyone decides how. `/design` plans against it, `/tdd` builds its scenarios, `/review`
checks tests against it, `/validate` checks acceptance against it.

## Where specs live
One folder per feature, the unit the roadmap names:

```
specs/<feature>/
  spec.md            # this skill
  <feature>.feature  # this skill (none for a technical feature)
  plan.md            # /design
  stepN-brief.md     # /feature-workflow
```

`<feature>` is kebab case and matches the roadmap item and the branch `feature/<feature>`.

## 1. spec.md

```markdown
# <Feature name>

**Status:** Draft | Approved | Done (CHANGELOG entry <date>)
**Roadmap:** <item, one line>

## Job
Who it is for and what it lets them do, in two or three sentences. The problem, not the solution.

## Scope
- In: …
- Out (non-goals): … — each with the reason, so it is not re-asked.

## Acceptance
- The scenarios in `<feature>.feature` (behavior), and
- measurable criteria a scenario cannot carry: a guard, a budget, a benchmark bound, an eval
  score, a count that must not change.

## Affected specs
Scenarios in other folders this feature adds, changes or removes, by folder and exact name.

## Open questions
Each one is answered by the user before approval, then moved into the text above.
```

A **technical feature** (performance, refactoring, tests, docs, layout) has a `spec.md` and no
`.feature`: its Acceptance is all measurable ("`make test` stays at N passed", "statement count
flat from 1 to 100 items", "p95 under X ms on the 10× world").

## 2. The feature file

```gherkin
Feature: Short Descriptive Name
  As a <role>
  I want to <capability>
  So that <business value>

  # Domain rules and non-obvious cases, as comments.

  Background:
    Given <shared preconditions>

  Scenario: One specific behavior
    Given <precondition>
    When <action>
    Then <observable outcome>
```

- **Behavior only.** What a user sees or what the system's state shows; no class names, no
  internals.
- **One behavior per scenario**, and scenario names unique across all specs: tests cite them by
  exact name.
- **Happy paths first, then errors, then edge cases** (ZOMBIES, `/tdd`).
- **Explicit ambient state.** A scenario that depends on the clock, randomness, env or the
  filesystem names the value in its `Given` ("Given the clock reads 14:00").
- **Audience-resolvable language.** Use the project's domain vocabulary; no references to
  private notes or agent prompts.
- **Tags:** only `@documented-only`, for a scenario that cannot be automated yet, with a comment
  saying why. A test's kind (unit, integration) is its path, not a tag.

## 3. Changes to existing behavior
A feature that changes what an existing scenario says edits that scenario **in its own folder**
and lists it under "Affected specs". Never copy a scenario into the new folder. A renamed or
removed scenario: find its citations (tests, design docs, ADRs) and list them for the plan, so
they change in the same feature.

## 4. Approval
Settle the open questions with the user (`AskUserQuestion`, previews for anything visual). Show
the spec, set **Status: Approved** when the user approves, and commit it on the feature branch.
Nothing is designed against a draft.

## Output
- The spec folder (path), the scenario count added / changed / removed.
- Affected specs and the citations a rename or removal breaks.
- Questions still open, if the user has not approved yet.

## What this skill is NOT
- Not test writing (`/tdd`) and not a coverage audit (`/review`).
- Not design: no layers, modules or ADRs here (`/design`).
