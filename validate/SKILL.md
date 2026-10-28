---
name: validate
description: Formal validation of a feature before merge — gate, spec acceptance, evals, benchmarks against the branch baseline, profile, render; "step" mode for a hot-path step
user_invocable: true
argument: The feature (specs/<feature>/), or "step" for a hot-path step's quick check
---

# Validate

`/review` checks each change cheaply. This skill is the heavy one: it proves a whole feature
meets its spec and costs no more than it did, before the user tries it and before the merge.
Its report is the evidence the changelog entry carries.

## Project settings
From the project CLAUDE.md "Workflow" section; with a setting missing, skip its check and say so.

| Setting | What it is |
|---|---|
| **Gate** | the command that must pass (lint, types, tests) |
| **Collect** | a count of opt-in tests that must match |
| **Evals** | the paid or slow checks a prompt, schema or model change must run, and their last scores |
| **Bench** | save a run, compare with a saved one, profile |
| **Render** | what to look at by hand on a scratch copy of real data |
| **Mutation** | the mutation sweep's command for named source files, and the check of the tool itself when the setting names one |
| **Protected files** | data never touched (copy it first) |

## Full mode (once per feature, on the feature branch, after the last step's commit)

Run in order; a failure stops the run, gets fixed (a fix is a step: brief or small fix, review),
and the run starts again from the top.

1. **Gate.** Record the test counts (per tree when there are several).
2. **Collect check.** The count matches the plan's.
3. **Spec acceptance.**
   - Every scenario of `specs/<feature>/` and of the "Affected specs" in its `spec.md` is cited
     by a test that runs in the gate (or is `@documented-only`, listed with its reason).
   - Every measurable criterion in "Acceptance" is measured here, with its number.
   - Scenarios removed from the spec leave no test or doc citing them.
4. **Evals.** When the feature changed a prompt, a tool schema, the vocabulary sent to the
   model or the model id: run the project's evals and compare with the last recorded scores.
   A drop is a finding, not a footnote.
5. **Benchmarks.** Compare with the baseline saved at the branch point (the roadmap's "Now"
   names it; with none, check out the branch point in a worktree and save one there).
   - A flagged benchmark is rerun alone before it is believed; look at both stddevs.
   - Benchmarks the feature cannot reach moving together is the machine: prove it with the
     interleaved A/B of `/perf` § 5 before calling it noise.
   - List every change over 10% either way.
6. **Profile.** For each flagged benchmark, or a new hot path with no benchmark yet: the
   project's profile command; name where the time went. A new hot path with no benchmark gets
   one (`/perf`), in this feature.
7. **Mutation.** The project's mutation command on every source file the feature changed
   (`git diff --name-only <branch point> -- <source root>`), after the tool's own check when the
   setting names one.
   - A survivor the project's list of equivalents does not explain is a finding: a test to write,
     dead code to delete, or an entry with its reason (`/mutants`, "Sorting survivors"), each made
     in this feature.
   - An entry no survivor matches any more (stale) is removed.
   - Re-render the list when the setting says how.
8. **Render.** The project's render items on a scratch copy of the real data: the views the
   feature changed, and one flow end to end per gateway it touched.

Then write `specs/<feature>/validation.md` and commit it:

```markdown
# <Feature> — validation (<date>, commit <sha>)
Gate: pass — N tests (unit U, integration I); before the feature: M
Collect: K (expected K)
Acceptance: S/S scenarios cited and passing; documented-only: …; criteria: <each with its number>
Evals: not needed (no prompt change) | <eval>: before → after
Benchmarks vs <baseline run>: no change over 10% | <name>: before → after (±x%), why
Profile: <where the time goes, for anything flagged>
Mutation: <files swept>: K killed, S known, 0 unexplained, 0 stale | not needed (no source file changed)
Render: <what was looked at, what it showed>
Still linear / left open: …
```

## Step mode (`/validate step`, a step the plan marks hot path)
Before the step's commit: the gate, then compare the benchmarks the plan names with the last
saved run (rerun a flagged one alone). Changes over 10% go in the step's commit message. After
the commit, save a run on it: a run saved before the commit carries the previous commit's name.

## Rules
- Timings never fail the gate; the deterministic guards in the gate do (`/design` § 2).
- Save a run only from a commit; never delete a run a comparison depends on.
- Generated data for benchmarks; real data only as a scratch copy, for rendering.
- No step is skipped silently: a check that does not apply says "not needed" and why.

## See also
- `/perf` — the method behind 5 and 6: baseline, audit, prototype, prove, compare.
- `/review` — the light per-change check.
- `/changelog` — copies this report into the feature's entry.
