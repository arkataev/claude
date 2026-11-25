---
description: Build a roadmap feature spec-first as the designer, with EGM goldfish reviews — spec checked by a fresh reader, plan by EGM's review loop (critic-egm and zoom-out), each brief by a readiness reviewer; writer and reviewer agents build; validate, changelog, merge. An A/B trial beside feature-workflow; needs the egm plugin
user_invocable: true
argument: The roadmap item to start, "resume", or "step N" of the feature in progress
---

# Feature Workflow with goldfish reviews (spec-driven; designer / goldfish / writer / reviewer)

This is the `feature-workflow` loop with EGM's goldfish reviews (the Elephant-Goldfish Model,
the `egm` plugin) added at the spec, the plan and each brief. It runs beside `feature-workflow` as
an A/B trial: the two share the project settings, `/bdd`, `/design`, `/tdd`, `/review`,
`/validate`, `/changelog`, `/roadmap` and the `writer` and `reviewer` agents. What differs is in
"Goldfish reviews (EGM)" below and in §§ 0–4.

The main session is the **designer** (EGM's "elephant"): it specs, plans, briefs, resolves
findings, reviews, validates and commits. Agents check and build. The goldfish reviewers each
start in a fresh context, with only the document and a reading list: `egm:egm-comprehension` reads
the spec, `critic-egm` (`~/.claude/agents/`) and `egm:egm-zoom-out` read the plan,
`egm:egm-implementation-readiness` reads each brief. The `writer` implements a brief, and a fresh
`reviewer` checks each step's diff. The agents never talk to each other or to the user;
everything goes through the designer. The designer writes no feature code beyond small fixes.

Why this split: the writer is cheap and focused (Sonnet, one brief at a time); the reviewer is
independent of the writer's reasoning (Opus, sees only the brief and the diff); the goldfish are
independent of the designer's reasoning and of each other's earlier rounds, so a document gets
read the way its next reader will read it, while a flaw in it costs a paragraph; the designer
keeps the whole picture and the user's decisions. Architecture stays with the designer: it needs
the conversation with the user, and every resolution and designer review rests on it.

## The loop

```
ROADMAP item ─► 0 Start: feature/<name>, baseline     [optional: /egm:egm-brainstorm]  (/roadmap start)
  1 Spec       specs/<name>/spec.md + .feature
               ─► comprehension goldfish ─► resolve           ◄ user approves  (/bdd)
  2 Plan       specs/<name>/plan.md, steps, hot-path flags
               ─► review loop: critic-egm + zoom-out, fresh each round, ≤3 rounds
               ─► resolve per round; the first clean round ends it ◄ user approves  (/design)
  3 Each step  brief ─► readiness goldfish ─► resolve ─► writer ─► fresh reviewer ─► triage
               ─► fix ─► designer review ─► [hot path: /validate step] ─► commit ─► roadmap Now
                                                                         (/tdd, /review)
  4 Validate   the whole feature, with the A/B numbers                    (/validate)
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
| **Test conventions**: test naming, citing scenarios, where tests live | the global TDD conventions |
| **Review checklist**: the project's invariants the critic and the reviewer check by name | the global architecture principles |
| **Designer review**: diffs the designer reads besides the core | none |
| **Evals**: paid or slow checks a prompt or model change runs (designer only) | none |
| **Bench**: save a run, compare with one, profile (`/perf`) | none |
| **Mutation**: the audit's command (and its form for named source files), its list of equivalents (an exemption list: a guard file), and the tool's own check | none |
| **Render**: what the designer looks at by hand on a scratch copy | none |
| **Specs / Roadmap / Changelog**: paths | `specs/`, `ROADMAP.md`, `CHANGELOG.md` |
| **Goldfish reading list (plan)**: what `egm:egm-zoom-out` reads besides the spec | the project's docs map and design doc (`docs/README.md`, `docs/design.md`) |
| **Goldfish reading list (brief)**: what `egm:egm-implementation-readiness` reads besides the brief | both CLAUDE.md files, the spec, the plan, every file the brief's "Read first" names and every existing file its "Changes" name |

## Goldfish reviews (EGM)

**The dependency.** The `egm` plugin (`claude plugin install egm@egm`; trial started on version
0.1.0, commit `403d888`). Its root is `installPath` of `egm@egm` in
`~/.claude/plugins/installed_plugins.json`; read it there, never guess a cache folder. If the
version is not the one above, stop and tell the user: an update is read like a dependency bump
(the diff of `skills/egm-review-loop`, `skills/egm-resolve`, `agents/{comprehension,zoom_out,implementation_readiness}.md`
and `resources/document_standards/{zoom-out,implementation-readiness}-standard.md`) before this
skill uses it, and then the version above is changed. The agent types `egm:egm-comprehension`,
`egm:egm-zoom-out` and `egm:egm-implementation-readiness` exist only in a session started after
the install; if one is missing, stop and say so. A review in the designer's context is not a
goldfish review.

**EGM's skills are followed, not invoked.** They set `disable-model-invocation`, so the Skill
tool refuses them. As EGM's `docs/claude.md` says, read `<root>/docs/claude.md` once, then read the
skill's `SKILL.md` from `<root>/skills/` and follow it in this session, with the changes listed
here and nothing else changed.

**A goldfish prompt** has only these lines, with absolute paths. No notes, no earlier findings,
no part of the conversation:
```
Mode: REVIEW
Persona: read <root>/agents/<persona>.md first.
TargetFile: <the document>
SemanticTarget: full file            (or the sections to re-check)
Standard: <root>/resources/document_standards/<standard>.md   (or none)
GoldfishContext: <the reading list>
```
The reading list is what the document's real reader has, no more: a goldfish keeps to it, so a
file it must check is on it. A goldfish cannot open URLs: save a page as a file first.

**Reports.** Each review writes EGM's `goldfish_review_report.md` (`egm-resolve` Step 3) into
its own folder of the feature, `specs/<name>/reviews/<point>/`, with `<point>` one of `spec`,
`plan`, `stepN-brief`; a later round of the same review replaces the file. The reports are
committed with the document they review.

| Point | Reviewers (agent type, persona) | Standard | Reading list | Rounds | Resolution |
|---|---|---|---|---|---|
| Spec (§ 1) | `egm:egm-comprehension`, `comprehension` | none | the `.feature` file and what the spec links; never a CLAUDE.md file or the plan | one pass | `egm-resolve`; its gate is the approval question |
| Plan (§ 2) | `critic-egm` (our agent, the plan path only) and `egm:egm-zoom-out`, `zoom_out` | zoom-out: `zoom-out-standard` | zoom-out: the spec, the `.feature` and the setting "Goldfish reading list (plan)"; the critic loads its own | `egm-review-loop`, one clean round converges, cap 3 | `egm-resolve`, its gate each round |
| Brief (§ 3) | `egm:egm-implementation-readiness`, `implementation_readiness` | `implementation-readiness-standard` | the setting "Goldfish reading list (brief)" | one pass; one fresh re-check after a Blocker fix | `egm-resolve` without its gate |

**Our changes to EGM**, the only ones:
1. **Direct dispatch.** The designer spawns each reviewer itself, never `egm:egm-synthesizer`:
   the synthesizer would spawn `critic-egm` as a general-purpose agent and lose its frontmatter
   (model, effort, the preloaded `design` skill), and it keeps findings only, where the user must
   see the comprehension paraphrase.
2. **`critic-egm` reads the CLAUDE.md files.** EGM's reviewers run without them
   (`omitClaudeMd`); the critic checks the project's rules by name, so it needs them. It stays a
   goldfish by being spawned fresh each round with the plan path alone.
3. **One clean round converges, cap 3** in `egm-review-loop` (Step 2.4), not two clean rounds
   and 5. Every other rule of its Step 2.4 holds: settled and fixed findings, what makes a round
   clean, churn. Why: round 1 nearly always has findings, so two clean rounds meant three rounds
   on almost every plan, and the third was a confirmation round of two fresh Opus reviewers (about
   $3 and 5 minutes in the pilot) that rarely finds anything. The cost of the change: a fix made
   after round 1 is confirmed by one fresh look, not two.
4. **The brief's readiness pass has no gate.** `egm-resolve` Steps 1–3 and 5 run as written; Step
   4 is replaced: the designer applies its PROPOSE FIX items, keeps CONTEST and DECLINE in the
   report, and asks the user about each ESCALATE item before the writer gets the brief (also when
   the user asked not to be pinged until the steps are done). Why: the user already starts each
   step, and a gate per brief would add a turn to every step.
5. **Reports go to the feature's folder** (above), not to the working directory.

## 0. Start
`/roadmap start <item>`: a clean, up-to-date `main`, then `git switch -c feature/<name>`, a
benchmark baseline saved on the branch point (with a Bench setting), the item in "Now" with
"workflow: egm" on its line. One feature per checkout. All of the feature's commits, spec and
plan included, are on its branch.

**Brainstorm (optional, the user's call).** For an item whose problem or direction is still
open, the user runs `/egm:egm-brainstorm` with the line `EGM artifact directory: specs/<name>/`
in the message. It writes `specs/<name>/concepts_brief.md`. At its last gate, pick "Conclude
brainstorming and keep brief for later": not "Publish … as RFC" (it writes `docs/designs/`) and
not `/egm-draft` (the spec and the plan are `/bdd` and `/design` here). Commit the brief with the
spec.

**Resume** (a new session): `git branch --list 'feature/*'`, switch to the one in progress, read
the roadmap's "Now" there, then the spec, the plan, the current brief and the reports under
`reviews/`.

## 1. Spec (`/bdd`)
Write or update `specs/<name>/spec.md` and its scenarios, and the scenarios of other specs the
feature changes; when `concepts_brief.md` exists, `/bdd` starts from it (its Goals, Non-Goals and
Alternatives Weighed). Settle the open questions with the user.

**Comprehension goldfish**, before the approval question: one pass of `egm:egm-comprehension` on
`spec.md` (the table above). Show the user its paraphrase ("What this proposes", "How the
existing system works, per this document") next to the spec: a wrong paraphrase is a finding,
and the user is the one who can tell. Resolve the findings by `egm-resolve` (report in
`reviews/spec/`); its gate is the approval question, so the user can accept fixes and approve in
one answer. A fresh second pass runs only when the user asks for one, after a large rewrite.

**Gate: the user approves the spec**; commit it with `reviews/spec/`. Nothing is planned against
a draft.

## 2. Plan (`/design`)
`specs/<name>/plan.md` against the approved spec: decisions, layers, data, ADR drafts, trace,
steps. Each step names its scenarios and whether it is a **hot path** (with the prototype numbers
it rests on, `/perf` § 3).

**Review loop:** before the user sees the draft, follow `egm-review-loop` with `TargetFile` the
plan, `SemanticTarget: full file`, `Reviewers: [critic-egm, zoom_out]`, `Standards: {zoom_out:
zoom-out-standard}` and the reading lists of the table, with our changes (direct dispatch, one
clean round converges, cap 3, the report in `reviews/plan/`). Spawn both reviewers of a round in one message, each a new agent;
never send a round to an earlier reviewer. Resolve each round by `egm-resolve`; the critic's
"Questions for the user" are ESCALATE items. The loop ends converged, or at the cap or on churn
with the open findings put to the user as `egm-review-loop` says. A plan amended after approval
(a step added, a decision changed) gets one more round on the amended sections
(`SemanticTarget` names them).

**Gate: the user approves the plan**; commit it with `reviews/plan/`. Then each step starts on
the user's "start".

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

A brief asks the writer for no mutation sweep: it costs minutes per file, whole files whatever
the diff, and is run again after every fix. The sweep is no step of a feature: it is an audit the
user asks for (`/mutants`, "The audit"). A brief that needs a survivor settled names its line, and the writer
checks it by hand (`/mutants`, "Checking one suspect").

**Readiness goldfish:** before the writer gets the brief, one pass of
`egm:egm-implementation-readiness` on it (the table above; report in `reviews/stepN-brief/`),
resolved by `egm-resolve` without its gate (our change 4). After a Blocker fix, one fresh pass
checks the brief again. The brief the writer gets is the resolved one; commit the report with the
step.

**Writer:** spawn once per feature with `subagent_type: "writer"` and the brief's path, plus
notes such as uncommitted user edits to leave alone. Reuse it with SendMessage for later steps
and the fix round; a resumed session spawns a new one. It works by `/tdd`. A bug a guard or the
validation finds after a step's commit is a new step with its own brief
(`stepN-fix-brief.md`), not a fix round.

**Reviewer:** spawn a new one for each step with `subagent_type: "reviewer"` and the brief's
path; reuse it with SendMessage only for that step's re-review. Its "next brief" follow-up is not
used here: a reviewer that saw earlier steps reads the new diff through them. It runs `/review`
on the step's diff.

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

`validation.md` ends with a **Workflow (A/B)** section, the numbers the comparison with
`feature-workflow` reads, all of them from git and the feature's folder:
- workflow: egm;
- spec and plan changes after approval: commits to `spec.md` or `plan.md` after their approval
  commits;
- fix briefs (`stepN-fix-brief.md`) and validation re-runs;
- the reviewer's Blocker and Major findings per step that trace back to the plan or the spec;
- goldfish runs: passes and plan-loop rounds, with how each loop ended (converged, cap, churn),
  and their Blocker / Major counts per point from the reports;
- the user's turns before the plan's approval.

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
through its commit, then validate and close, and ping once before the merge; an ESCALATE item of
a brief's readiness pass still stops the run for the user's answer.

## Setting up a new project
Add a "Workflow" section to the project's `CLAUDE.md` with the settings above that differ from
the defaults, and create `ROADMAP.md` (`/roadmap`) and an empty `CHANGELOG.md`. A project agent
with the same name (`.claude/agents/writer.md`) replaces the global one completely, so put
project specifics in the settings, not in a copied agent. Install the `egm` plugin and allow
reads of its `agents/`, `docs/`, `resources/` and `skills/` folders (EGM's `docs/claude.md`),
then start a new session so its agent types load.
