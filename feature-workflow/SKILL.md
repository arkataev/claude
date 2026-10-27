---
description: Build a roadmap feature spec-first as the designer — spec, plan, steps by the writer and reviewer agents, validate, changelog, merge
user_invocable: true
argument: The roadmap item to start, "resume", or "step N" of the feature in progress
---

# Feature Workflow (spec-driven; designer / writer / reviewer)

The main session is the **designer**: it specs, plans, briefs, triages, reviews, validates and
commits. Two global agents do the rest, `writer` and `reviewer` (`~/.claude/agents/`). They never
talk to each other or to the user; everything goes through the designer. The designer writes no
feature code beyond small fixes.

Why this split: the writer is cheap and focused (Sonnet, one brief at a time), the reviewer is
independent of the writer's reasoning (Opus, sees only the brief and the diff), and the designer
keeps the whole picture and the user's decisions.

## The loop

```
ROADMAP item ─► 0 Start: feature/<name>, baseline                          (/roadmap start)
  1 Spec       specs/<name>/spec.md + .feature              ◄ user approves  (/bdd)
  2 Plan       specs/<name>/plan.md, steps, hot-path flags  ◄ user approves  (/design)
  3 Each step  brief ─► writer ─► reviewer ─► triage ─► fix ─► designer review
               ─► [hot path: /validate step] ─► commit ─► roadmap Now     (/tdd, /review)
  4 Validate   the whole feature                                          (/validate)
  5 Close      CHANGELOG entry, roadmap updated                           (/changelog)
  6 Merge      user tries it ─► git merge --no-ff ─► delete the branch
```

## Project settings
The project's `CLAUDE.md`, section "Workflow". The agents read the same section. Where an item
is missing, use the default.

| Setting | Default |
|---|---|
| **Gate**: the one command that must pass (lint, types, tests) | the project's test command |
| **Collect check**: a count of opt-in or expensive tests that must match the plan | none |
| **Off-limits**: runs the agents never make (paid APIs, services, bots) | anything that hits the network or a paid API |
| **Protected files**: data never touched | none |
| **Brief extras**: numbers or lists every brief states | none |
| **Test conventions**: test naming, citing scenarios, where tests live | the global TDD conventions |
| **Review checklist**: the project's invariants the reviewer checks by name | the global architecture principles |
| **Evals**: paid or slow checks a prompt or model change runs (designer only) | none |
| **Bench**: save a run, compare with one, profile (`/perf`) | none |
| **Render**: what the designer looks at by hand on a scratch copy | none |
| **Specs / Roadmap / Changelog**: paths | `specs/`, `ROADMAP.md`, `CHANGELOG.md` |

## 0. Start
`/roadmap start <item>`: a clean, up-to-date `main`, then `git switch -c feature/<name>`, a
benchmark baseline saved on the branch point (with a Bench setting), the item in "Now". One
feature per checkout. All of the feature's commits, spec and plan included, are on its branch.

**Resume** (a new session): `git branch --list 'feature/*'`, switch to the one in progress, read
the roadmap's "Now" there, then the spec, the plan and the current brief.

## 1. Spec (`/bdd`)
Write or update `specs/<name>/spec.md` and its scenarios, and the scenarios of other specs the
feature changes. Settle the open questions with the user. **Gate: the user approves the spec**;
commit it. Nothing is planned against a draft.

## 2. Plan (`/design`)
`specs/<name>/plan.md` against the approved spec: decisions, layers, data, ADR drafts, trace,
steps. Each step names its scenarios and whether it is a **hot path** (with the prototype numbers
it rests on, `/perf` § 3). **Gate: the user approves the plan**; commit it. Then each step starts
on the user's "start".

## 3. Each step

**Brief:** `specs/<name>/stepN-brief.md`:
- **Status**: what is done and what this step does.
- **Read first**: files and docs, in order.
- **Changes**: numbered, each with its file and its layer.
- **Scenarios and tests**: the scenarios this step builds (by exact name, from the spec), then
  the tests that cite them. A step that changes where an error is raised (a new place it can
  come from, or a check that moves) lists every caller up to the gateways and asks for a gateway
  test of the scenario's outcome, not only a test where the error starts. A store test of a new
  `Busy` once passed while the bot dropped the update with no reply.
- **Docs to update.**
- **This step's numbers**: the project's brief extras; for a hot-path step, the benchmarks
  expected to move.

The standing rules (off-limits runs, no git writes, no secrets, protected files) and the report
formats live in the agent definitions and the project's settings, not in each brief.

**Writer:** spawn once per feature with `subagent_type: "writer"` and the brief's path, plus
notes such as uncommitted user edits to leave alone. Reuse it with SendMessage for later steps
and the fix round. It works by `/tdd`.

**Reviewer:** spawn and reuse the same way with `subagent_type: "reviewer"` and the brief's path.
It runs `/review` on the step's diff.

**Triage:** accept or reject each finding and say why. Send the accepted ones to the writer: one
review round, one fix round. Make small fixes inline. Optionally send the fixes back to the
reviewer for a re-review of only those findings.

**Designer review**, after the fix round and before the commit, against the `/design` rules:
- values are built whole and constructed on the value;
- data access is designed as if remote, concurrent and failing;
- layers point one way;
- gateways only represent; they decide nothing.

Fix what breaks a rule, or send it back to the writer. A step is not committed on the
reviewer's word alone. Read the core diff (domain, persistence, services, shared wording) and
run the gate and the collect check.

**Hot-path step:** `/validate step` before the commit (benchmark changes over 10% go in the
commit message), and a run saved after it.

**Commit** on the feature branch with the step's numbers (test counts; scores and benchmark
changes when measured), then update the roadmap's "Now" (`/roadmap now`) in the same commit.

## 4. Validate (`/validate`)
After the last step: the full run, `specs/<name>/validation.md` committed. A failure is fixed as
a step (brief or small fix, review) and the validation starts again.

## 5. Close (`/changelog`)
The entry in `CHANGELOG.md`, the roadmap updated (item done, follow-ups added), the spec's status
`Done`; committed on the branch.

## 6. Merge
Ping the user with what to try (from the entry). After they have tried it:
`git switch main && git merge --no-ff feature/<name>`, with the message
`Merge feature/<name>: <one line>` and a pointer to the changelog entry; then
`git branch -d feature/<name>`. The entry names the branch, so `git log --merges --grep
feature/<name>` finds the merge; nothing is committed on `main` after it.

**Autonomy:** the spec and the plan are always approved by the user. Each step starts on the
user's "start". When the user says "don't ping me until all steps are done", run every step
through its commit, then validate and close, and ping once before the merge.

## Setting up a new project
Add a "Workflow" section to the project's `CLAUDE.md` with the settings above that differ from
the defaults, and create `ROADMAP.md` (`/roadmap`) and an empty `CHANGELOG.md`. A project agent
with the same name (`.claude/agents/writer.md`) replaces the global one completely, so put
project specifics in the settings, not in a copied agent.
