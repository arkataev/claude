---
description: The CI pilot of solid-workflow — the same loop with one PR per step on GitHub, each step held by the step scorecard (the project's gate, size, scenarios, public interface) and reviewed by solid-reviewer-ci in CI on a /review comment; solid-critic-ci sizes the steps, solid-writer-ci keeps to the budget. A trial beside solid-workflow; needs the flow repo's pilot branch (ci/PILOT.md)
user_invocable: true
argument: The roadmap item to start, "resume", or "step N" of the feature in progress
---

# Solid workflow, CI pilot (spec-driven; designer / critic / writer / reviewer)

This is `/solid-workflow` with one PR per step on GitHub, a trial beside it (the flow repo's
`ci/PILOT.md`). Each step is a branch and a PR into the feature branch. The step scorecard checks
it in CI with no model (the project's gate, the step's size, the scenarios' tests, the public
interface), and `solid-reviewer-ci` reviews it in CI on a `/review` comment. The plan marks each
step's size, and the writer stops at the budget instead of squeezing the code. Everything else is
`/solid-workflow` as written. It is `/feature-workflow` with the solid rules: the same loop, and
it shares the project settings, `/bdd`, `/validate`, `/changelog`, `/roadmap`, `/mutants` and
`/perf`. What differs is the rule set and who carries it:

| Role | Here | Loads |
|---|---|---|
| Designer (the main session) | — | `/solid-design` and `solid-principles` |
| Critic | `solid-critic-ci` | `solid-design`, `solid-principles` |
| Writer | `solid-writer-ci` | `solid-tdd`, `mutants`, `solid-principles` |
| Reviewer | `solid-reviewer-ci`, in CI | `solid-review`, `mutants`, `solid-principles` |

At the start, load `/solid-design` and `solid-principles` in the main session. Where they
differ from the global `CLAUDE.md`, they win (`solid-principles`, "Precedence"): a pure
domain, adapters that own their interface and model, a service that maps between them,
adapters tested at the composition layer only. A feature runs in one flow from start to merge.
It never switches to `/feature-workflow` or `/solid-workflow` halfway.

The main session is the **designer**: it specs, plans, briefs, triages, reviews, validates and
commits. Three global agents check and build (`~/.claude/agents/`): `solid-critic-ci` checks
the plan, `solid-writer-ci` implements a brief, `solid-reviewer-ci` checks the step's PR in CI. They never
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
  2 Plan       specs/<name>/plan.md, steps with sizes, hot-path flags
               ─► solid-critic-ci ─► triage                 ◄ user approves  (/solid-design)
  3 Each step  brief ─► step/<name>/<N> ─► solid-writer-ci ─► commit, step PR
               ─► scorecard (CI) ─► /review: solid-reviewer-ci (CI) ─► triage ─► fix
               ─► designer review ─► [hot path: /validate step] ─► merge into feature/<name>
               ─► roadmap Now                                      (/solid-tdd, /solid-review)
  4 Validate   the whole feature                                          (/validate)
  5 Close      CHANGELOG entry, roadmap updated                           (/changelog)
  6 Merge      feature PR, scorecard green ─► user tries it ─► merge commit ─► delete branches
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
| **CI**: the repo's callers of the flow's `scorecard.yml` and `review.yml`, with their `source`, `tests`, `setup` and `gate` inputs | none: without them, run `/solid-workflow` |

## 0. Start
`/roadmap start <item>`: a clean, up-to-date `main`, then `git switch -c feature/<name>`, a
benchmark baseline saved on the branch point (with a Bench setting), the item in "Now". One
feature per checkout. All of the feature's commits, spec and plan included, are on its branch.
Push the branch: each step's PR goes into it.

**Resume** (a new session): `git branch --list 'feature/*'`, switch to the one in progress, read
the roadmap's "Now" there, then the spec, the plan and the current brief, then the open step PR
(`gh pr list --base feature/<name>`): its scorecard, its review and the replies on it.

## 1. Spec (`/bdd`)
Write or update `specs/<name>/spec.md` and its scenarios, and the scenarios of other specs the
feature changes. Settle the open questions with the user. **Gate: the user approves the spec**;
commit it. Nothing is planned against a draft.

## 2. Plan (`/solid-design`)
`specs/<name>/plan.md` against the approved spec: decisions, layers, data, ADR drafts, trace,
steps. Each step names its scenarios and whether it is a **hot path** (with the prototype numbers
it rests on, `/perf` § 3), its **size** (small, medium or large; no line counts: the scorecard
counts, after the fact), and **every public name it adds, changes or removes** (the interface check
reads them there). A large step names its natural seam, or why it has none: a step is a vertical
slice that adds behavior and passes its scenarios, and it is never cut to fit a size. The plan
cites the Shape rules of `solid-principles` it settles. Its
module map shows the import graph: the domain, each adapter and the service that maps between
them (D1–D3). Its steps put each test at its layer (V1).

**Critic:** before the user sees the draft, spawn `subagent_type: "solid-critic-ci"` with the plan's path,
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
- **Size**: the plan's mark, and the budget: source lines only (the CI's `source` globs), a
  warning over 400 and the cap at 800; tests do not count. Over the budget, the writer stops and
  reports; it does not compress the code.
- **Interface**: the public names the step adds, changes or removes, as the plan names them;
  "none" when there are none. The writer changes no other.
- **This step's numbers**: the project's brief extras; for a hot-path step, the benchmarks
  expected to move.

The standing rules (off-limits runs, no git writes, no secrets, protected files) and the report
formats live in the agent definitions and the project's settings, not in each brief.

A brief asks the writer for no mutation sweep: it costs minutes per file, whole files whatever
the diff, and is run again after every fix. The sweep is no step of a feature: it is an audit the
user asks for (`/mutants`, "The audit"). A brief that needs a survivor settled names its line, and the writer
checks it by hand (`/mutants`, "Checking one suspect").

**Step branch:** before the writer starts, `git switch -c step/<name>/<N> feature/<name>`. A
branch `feature/<name>/stepN` cannot exist beside `feature/<name>` in git, so steps live under
`step/`.

**Writer:** spawn once per feature with `subagent_type: "solid-writer-ci"` and the brief's path, plus
notes such as uncommitted user edits to leave alone. Reuse it with SendMessage for later steps
and the fix round; a resumed session spawns a new one. It works by `/solid-tdd`. A shape breach
it raises as an open item (a Code rule that only a shape change can meet) goes to the user. A bug a guard or the
validation finds after a step's commit is a new step with its own brief
(`stepN-fix-brief.md`), not a fix round.

**Step PR:** commit the writer's change on the step branch (`Step N of <name>: <one line>`, with
its numbers), push, and open the PR into `feature/<name>` (`gh pr create --base feature/<name>`).
Its description names the brief and, when the brief's Interface list is not "none", has the line
`Interface change: specs/<name>/`. A `size-exempt` label and its `Size exempt: <reason>` line go
in only on the user's word. Wait for the scorecard (`gh run watch` on its run, in the background):
a red gate, size, scenario or interface row is fixed before the review, since a failed gate skips
it anyway.

**Reviewer:** comment `/review specs/<name>/stepN-brief.md` on the step PR. The CI runs the gate
once, then `solid-reviewer-ci`, and posts one review; wait for its run, then read the findings
(`gh run download <run> -n findings`, `findings.json`). If CI cannot run, spawn
`subagent_type: "solid-reviewer-ci"` locally on the uncommitted diff instead, as in
`/solid-workflow`.

**Triage:** accept or reject each finding and say why, as a reply on its PR comment: `accept`, or
`reject: <reason>`. The replies are the saved triage. Send the accepted ones to the writer: one
review round, one fix round. Make small fixes inline. Commit the fixes, push, and let the
scorecard run again; optionally comment `/review` again for a re-review.

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
the diff of the guard files, and run the collect check; the scorecard's gate row is the gate. A
loosened check goes in only when the brief asked for it, with its reason in the commit message.

**Candidate guards:** a finding the reviewer marks as one a linter rule or a guard could have
caught, and one that comes back across steps, is a roadmap item for a guard (`/roadmap`), not a
reminder in the next brief.

**Hot-path step:** `/validate step` before the commit (benchmark changes over 10% go in the
commit message), and a run saved after it.

**Merge the step** once the scorecard is green and the designer review is done: update the
roadmap's "Now" (`/roadmap now`) on the step branch, push, then
`gh pr merge <PR> --merge --delete-branch`. The merge commit keeps the step's commits and its
numbers (test counts; scores and benchmark changes when measured) on the feature branch.

## 4. Validate (`/validate`)
After the last step: the full run, `specs/<name>/validation.md` committed. A failure is fixed as
a step (brief or small fix, review) and the validation starts again.

## 5. Close (`/changelog`)
The entry in `CHANGELOG.md`, the roadmap updated (item done, follow-ups added), the spec's status
`Done`; committed on the branch.

## 6. Merge
Open the feature's PR into `main` (`gh pr create --base main --head feature/<name>`); it holds no
unreviewed code, since every step was a reviewed PR. Its scorecard also checks that every scenario
of the feature has its test. Ping the user with what to try (from the entry) and the PR. After
they have tried it: `gh pr merge <PR> --merge --delete-branch`, titled
`Merge feature/<name>: <one line>`, with a pointer to the changelog entry in its body. A merge
commit is the `--no-ff` merge; the entry names the branch, so `git log --merges --grep
feature/<name>` finds it; nothing is committed on `main` after it.

**Autonomy:** the spec and the plan are always approved by the user. Each step starts on the
user's "start". When the user says "don't ping me until all steps are done", run every step
through its commit, then validate and close, and ping once before the merge.

## Setting up a new project
Add a "Workflow" section to the project's `CLAUDE.md` with the settings above that differ from
the defaults, and create `ROADMAP.md` (`/roadmap`) and an empty `CHANGELOG.md`. Push the repo to
GitHub and add the two callers (`ci/PILOT.md`, "Setting it up for a project"), with
`agent: solid-reviewer-ci` in the review caller, and the secret `CLAUDE_CODE_OAUTH_TOKEN`. Copy the Ruff
and mypy sections of `~/.claude/skills/solid-principles/baseline.toml` into `pyproject.toml`
(a guard-file change the user approves). A project agent with the same name
(`.claude/agents/solid-writer-ci.md`) replaces the global one completely, so put project specifics
in the settings, not in a copied agent.

A project can run several flows, one per feature, chosen at `/roadmap start`. A feature built
with this flow keeps its solid shape, and the next feature on the same code takes a solid flow
unless the user says otherwise.
