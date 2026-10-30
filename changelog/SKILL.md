---
name: changelog
description: Close a feature — write its CHANGELOG.md entry from the spec, the commits and the validation report, and move what is left to the roadmap
user_invocable: true
argument: The feature (specs/<feature>/)
---

# Changelog

The changelog says **what has been done**; the roadmap (`/roadmap`) says what will be done next.
A reader who opens only `CHANGELOG.md` learns what the project can do now, since when, and what
it cost. It replaces handover notes: work in progress lives in the roadmap's "Now", never here.

## When
On the feature branch, after `/validate` passed and before the user tries it, so the entry is
part of what is merged. The merge commit's message points back to the entry.

## Sources (read, don't recall)
- `specs/<feature>/spec.md` (job, acceptance, affected specs) and `plan.md` (decisions, ADRs).
- `git log --oneline main..HEAD` and `git diff --stat main...HEAD`.
- `git diff main...HEAD -- 'specs/**/*.feature'` for the scenarios added, changed, removed.
- `specs/<feature>/validation.md` for the numbers.
- The briefs' and reports' open items, for the follow-ups.

## Entry (top of `CHANGELOG.md`, newest first)

```markdown
## <Feature name> — <YYYY-MM-DD>
Branch `feature/<feature>` (<first sha>..<last sha>) · spec `specs/<feature>/`

<Two or three sentences: what a user can do now that they could not, or what changed for the
maintainer. The job, not the steps.>

**Behavior** (scenarios)
- Added: «<exact scenario name>», … (<spec folder>)
- Changed: «…» — what changed in it
- Removed: «…» — why

**Structure**
- ADR-N <title>: the decision in one line
- New modules or layers; guards added

**Operations**
- Commands, settings, environment, migrations, dependencies a user or operator must know

**Numbers** (from validation.md)
- Tests: before → after (per tree)
- Benchmarks: every change over 10%, before → after; or "no change over 10%"
- Evals: before → after, when run

**Known limits**
- What it does not do, or does badly, on purpose or for now

**Follow-ups** → ROADMAP.md
- Each one also added to the roadmap, with where it came from
```

Rules:
- Facts with their numbers; no narrative of how it was built (that is the git log and the
  briefs). No "simply", "just", no praise.
- Scenario names exact, so a reader can find them; ADRs by number.
- An empty section is left out, except Numbers.
- The entry is append-only once merged: a correction is a new entry or a dated note under it.

## Then compact the spec folder
Once the entry is written, `specs/<feature>/` says what was built, not how it got there; the
history stays in git:
- `spec.md`: the job, scope, acceptance and affected specs; settled questions and restated
  reasons are dropped.
- `plan.md`: the design as built: the decisions still true, modules, data model, interfaces,
  data access, the trace, and any list another document points to. The step table, decisions
  taken back, and ADR drafts now in the design doc go.
- `validation.md`: the last validation's numbers and what is left open; earlier re-runs go.
- The briefs are deleted.

Every pointer into the folder (roadmap, changelog, ADR references) still resolves afterwards.

## Then the roadmap
Through `/roadmap`: mark the item done (it leaves Now/Next, pointing to this entry), add each
follow-up, and update "To confirm with the user" with questions the feature raised. Set the
spec's status to `Done (CHANGELOG <date>)`. Commit them, and the compacted spec folder, with the
entry.

## Output
The entry, the roadmap diff, and what the user should try before the merge.
