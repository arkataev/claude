---
description: Build a roadmap feature spec-first with the solid rules — the designer plans by solid-design and the solid-principles catalog (pure domain, adapters own their model, a service maps, tests by layer); solid-critic checks the plan, solid-writer and solid-reviewer build each step; validate, changelog, merge. Runs beside feature-workflow
user_invocable: true
argument: The roadmap item to start, "resume", or "step N" of the feature in progress
---

# Solid workflow (spec-driven; designer / critic / writer / reviewer)

This is `/feature-workflow` with the solid rules. It is the same loop, and it shares the
project settings, `/bdd`, `/validate`, `/changelog`, `/roadmap`, `/mutants` and `/perf`. What
differs is the rule set and who carries it:

| Role | Here | Loads |
|---|---|---|
| Designer (the main session) | — | `/solid-design` and `solid-principles` |
| Critic | `solid-critic` | `solid-design`, `solid-principles` |
| Writer | `solid-writer` | `solid-tdd`, `mutants`, `solid-principles` |
| Reviewer | `solid-reviewer` | `solid-review`, `mutants`, `solid-principles` |

At the start, load `/solid-design` and `solid-principles` in the main session. Where they
differ from the global `CLAUDE.md`, they win (`solid-principles`, "Precedence"): a pure
domain, adapters that own their interface and model, a service that maps between them,
adapters tested at the composition layer only. A feature runs in one flow from start to merge.
It never switches to `/feature-workflow` halfway.

The main session is the **designer**: it specs, plans, briefs, triages, reviews, validates and
commits. Three global agents check and build (`~/.claude/agents/`): `solid-critic` checks the
plan, `solid-writer` implements a brief, `solid-reviewer` checks the writer's diff. They never
talk to each other or to the user; everything goes through the designer. The designer writes no
feature code beyond small fixes.

Why this split: the writer is cheap and focused (Sonnet, one brief at a time); the reviewer is
independent of the writer's reasoning (Opus, sees only the brief and the diff); the critic is
independent of the designer's (Opus, sees only the spec, the plan and the code), so a plan gets
the same second look as a diff, while a flaw in it costs a paragraph; the designer keeps the
whole picture and the user's decisions. Architecture stays with the designer: it needs the
conversation with the user, and every triage and designer review rests on it.

## The loop

```
ROADMAP item ─► 0 Start: feature/<name>, baseline                          (/roadmap start)
  1 Spec       specs/<name>/spec.md + .feature              ◄ user approves  (/bdd)
  2 Plan       specs/<name>/plan.md, steps, hot-path flags
               ─► solid-critic ─► triage                    ◄ user approves  (/solid-design)
  3 Each step  brief ─► solid-writer ─► solid-reviewer ─► triage ─► fix ─► designer review
               ─► [hot path: /validate step] ─► commit ─► roadmap Now  (/solid-tdd, /solid-review)
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
| **Format**: the command that applies formatting and auto-fixable lint | none |
| **Guard files**: linter, type and import config, guard tests, test fences: what no agent loosens unless the brief says so | the linter and type-checker config |
| **Collect check**: a count of opt-in or expensive tests that must match the plan | none |
| **Off-limits**: runs the agents never make (paid APIs, services, bots) | anything that hits the network or a paid API |
| **Protected files**: data never touched | none |
| **Brief extras**: numbers or lists every brief states | none |
| **Read first**: docs an agent reads before its first task, per agent | the brief's list |
| **Test conventions**: test naming, citing scenarios, where tests live | `/solid-tdd` and `solid-principles` V1 |
| **Review checklist**: the project's invariants the critic and the reviewer check by name | the global architecture principles, as `solid-principles` amends them |
| **Designer review**: diffs the designer reads besides the core | none |
| **Evals**: paid or slow checks a prompt or model change runs (designer only) | none |
| **Bench**: save a run, compare with one, profile (`/perf`) | none |
| **Mutation**: the audit's command (and its form for named source files), its list of equivalents (an exemption list: a guard file), and the tool's own check | none |
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

## 2. Plan (`/solid-design`)
`specs/<name>/plan.md` against the approved spec: decisions, layers, data, ADR drafts, trace,
steps. Each step names its scenarios and whether it is a **hot path** (with the prototype numbers
it rests on, `/perf` § 3). The plan cites the Shape rules of `solid-principles` it settles. Its
module map shows the import graph: the domain, each adapter and the service that maps between
them (D1–D3). Its steps put each test at its layer (V1).

**Critic:** before the user sees the draft, spawn `subagent_type: "solid-critic"` with the plan's path,
plus notes such as decisions the user already made. Triage its findings as a step's: fix the
blocking ones and the gaps you accept in the plan, and put its questions for the user to the
user. Show the user the plan with the findings you rejected, one line each with why. A revision
that answers blocking findings goes back to the same critic for a re-check (SendMessage). A plan
amended after approval (a step added, a decision changed) gets a re-check of the amended
sections.

**Gate: the user approves the plan**; commit it. Then each step starts on the user's "start".

## 3. Each step

**Brief:** `specs/<name>/stepN-brief.md`:
- **Status**: what is done and what this step does.
- **Read first**: files and docs, in order.
- **Changes**: numbered, each with its file and its layer.
- **Rules**: the rule IDs of `solid-principles` the step touches. The shape the step fixes is
  its interfaces, its owners, and where each rule and each mapping lives.
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

A brief asks the writer for no mutation sweep: it costs minutes per file, whole files whatever
the diff, and is run again after every fix. The sweep is no step of a feature: it is an audit the
user asks for (`/mutants`, "The audit"). A brief that needs a survivor settled names its line, and the writer
checks it by hand (`/mutants`, "Checking one suspect").

**Writer:** spawn once per feature with `subagent_type: "solid-writer"` and the brief's path, plus
notes such as uncommitted user edits to leave alone. Reuse it with SendMessage for later steps
and the fix round; a resumed session spawns a new one. It works by `/solid-tdd`. A shape breach
it raises as an open item (a Code rule that only a shape change can meet) goes to the user. A bug a guard or the
validation finds after a step's commit is a new step with its own brief
(`stepN-fix-brief.md`), not a fix round.

**Reviewer:** spawn and reuse the same way with `subagent_type: "solid-reviewer"` and the brief's path.
It runs `/solid-review` on the step's diff.

**Triage:** accept or reject each finding and say why. Send the accepted ones to the writer: one
review round, one fix round. Make small fixes inline. Optionally send the fixes back to the
reviewer for a re-review of only those findings.

**Designer review**, after the fix round and before the commit, against the `/solid-design` rules:
- values are built whole and constructed on the value;
- data access is designed as if remote, concurrent and failing;
- layers point one way, and the import graph holds:
  - the domain and the adapters import nothing of the app;
  - only the service maps between them (D1–D3);
- each test is at its layer, and the composition tests run in-process (V1);
- gateways only represent; they decide nothing.

Fix what breaks a rule, or send it back to the writer. A step is not committed on the
reviewer's word alone. Read the core diff (domain, persistence, services, shared wording) and
the diff of the guard files, and run the gate and the collect check. A loosened check goes in
only when the brief asked for it, with its reason in the commit message.

**Candidate guards:** a finding the reviewer marks as one a linter rule or a guard could have
caught, and one that comes back across steps, is a roadmap item for a guard (`/roadmap`), not a
reminder in the next brief.

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
the defaults, and create `ROADMAP.md` (`/roadmap`) and an empty `CHANGELOG.md`. Copy the Ruff
and mypy sections of `~/.claude/skills/solid-principles/baseline.toml` into `pyproject.toml`
(a guard-file change the user approves). A project agent with the same name
(`.claude/agents/solid-writer.md`) replaces the global one completely, so put project specifics
in the settings, not in a copied agent.

A project can run both flows, one per feature, chosen at `/roadmap start`. A feature built with
this flow keeps its solid shape, and the next feature on the same code takes the same flow
unless the user says otherwise.
