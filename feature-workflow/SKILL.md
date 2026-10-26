---
description: Build a feature as the designer — plan, brief each step, hand it to the writer agent, have the reviewer agent check it, triage, verify, commit
user_invocable: true
argument: The feature to build, or "step N" of an existing plan
---

# Feature Workflow (designer / writer / reviewer)

The main session is the **designer**: it plans, briefs, triages, reviews and commits. Two
global agents do the rest, `writer` and `reviewer` (`~/.claude/agents/`). They never talk to each
other or to the user; everything goes through the designer. The designer writes no feature code
beyond small fixes.

Why this split: the writer is cheap and focused (Sonnet, one brief at a time), the reviewer is
independent of the writer's reasoning (Opus, sees only the brief and the diff), and the designer
keeps the whole picture and the user's decisions. A separate context-reader agent was tried and
judged not worth it: Haiku only for broad read-only lookups.

## Project settings
Each project states its settings in its `CLAUDE.md`, section "Workflow". The agents read the
same section. When an item is missing, use the default.

| Setting | Default |
|---|---|
| **Gate**: the one command that must pass (lint, types, tests) | the project's test command |
| **Collect check**: a count of opt-in or expensive tests that must match the brief | none |
| **Off-limits**: runs the agents never make (paid APIs, services, bots) | anything that hits the network or a paid API |
| **Protected files**: data never touched | none |
| **Brief extras**: numbers or lists every brief states | none |
| **Test conventions**: test naming, citing scenarios, where tests live | the global TDD conventions |
| **Review checklist**: the project's invariants the reviewer checks by name | the global architecture principles |
| **Verify**: what the designer checks or renders by hand before a commit | the gate |
| **Bench**: the commands that save a benchmark run and compare one against it (`/perf`) | none |
| **State file**: where "Resume here" lives | none |

## 1. Plan
Run `/design` into `docs/<feature>-plan.md`: the job, layers, data and invariants, validation
placement, ADR drafts, a trace, and the steps. Settle the user's decisions with
`AskUserQuestion` (previews for anything visual). Commit the plan and wait for "start".

## 2. Brief (one per step)
`docs/<feature>-stepN-brief.md`:
- **Status**: what is done and what this step does.
- **Read first**: files and docs, in order.
- **Changes**: numbered, each with its file and its layer.
- **Spec and tests**: scenarios first (`features/*.feature`), then the tests that cite them.
- **Docs to update.**
- **This step's numbers**: the project's brief extras; with a Bench setting and a step on a hot
  path, the benchmarks expected to move and the prototype numbers the plan rests on.

The standing rules (off-limits runs, no git writes, no secrets, protected files) and the report
formats live in the agent definitions and the project's settings, not in each brief.

With a Bench setting, save a baseline run on the commit before the writer starts and name it in
the brief.

## 3. Writer
Spawn once per feature with `subagent_type: "writer"` and the brief's path, plus notes such as
uncommitted user edits to leave alone. Reuse it with SendMessage for later steps and the fix
round. It implements test-first: a scenario's test fails before its code, and a test that passes
at once is checked by breaking the code.

## 4. Reviewer
Spawn and reuse the same way with `subagent_type: "reviewer"` and the brief's path. It checks
scenarios against tests, runs `/code-review`, and verifies each finding. Findings come ranked by
severity, each with a concrete failure scenario. New SQL comes with its query plan checked; a
new loop over stored data, with a benchmark at two sizes; a new external call, within the call
budget; a new write entry point, in the idempotency and fault-injection guards (where the
project has them).

## 5. Triage
Accept or reject each finding and say why. Send the accepted ones to the writer: one review
round, one fix round. Make small fixes inline. Optionally send the fixes back to the reviewer
for a re-review of only those findings.

## 6. Final review (the designer, every step)
After the fix round and before committing, review the step yourself against the `/design` rules:
- values are built whole and constructed on the value;
- data access is designed as if remote, concurrent and failing;
- layers point one way;
- gateways only represent; they decide nothing.

Fix what breaks a rule, or send it back to the writer. A step is not committed on the
reviewer's word alone.

## 7. Verify and commit
Read the core diff (domain, persistence, services, shared wording), run the gate and the collect
check, then do the project's verify items. With a Bench setting, compare against the baseline
after the fix round: rerun a flagged benchmark alone before calling it noise, then save the run.
Commit with the step's numbers in the message (scores, test counts, benchmark changes over
10%). Update the project's state file.

## 8. Ping the user
Say what to try. Merge to `main` (fast-forward) only after they have tried it.

**Autonomy:** confirm "start" with the user before each step. When the user says "don't ping me
until all steps are done", run every step through commit without waiting between steps and ping
once at the end.

## Setting up a new project
Add a "Workflow" section to the project's `CLAUDE.md` with the settings above that differ from
the defaults. A project agent with the same name (`.claude/agents/writer.md`) replaces the global
one completely, so put project specifics in the settings, not in a copied agent.
