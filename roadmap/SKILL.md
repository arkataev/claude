---
name: roadmap
description: Keep ROADMAP.md — the project's current scope: what is in progress, what comes next, what is still to confirm; start a feature from it
user_invocable: true
argument: "show" (default), "add <item>", "refine", "reorder", "start <item>", or "now" to update the in-progress state
---

# Roadmap

`ROADMAP.md` says **what will be done**; `CHANGELOG.md` (`/changelog`) says what has been done.
It is the project's current scope and the first thing a new session reads after `CLAUDE.md`:
its "Now" is where work resumes. Refine it whenever development teaches something.

## Format

```markdown
# Roadmap

## Now
**<feature>** — `feature/<feature>` · spec `specs/<feature>/` (Draft | Approved)
- Plan: <Draft | Approved>; step <k> of <n>: <what it does>, <state: briefed | writing | in review | committed <sha>>
- Baseline: bench run <id> on <sha> (the branch point)
- Gate: <N> tests at the last commit; collect <K>
- Next action: <one line a fresh session can act on>
- Open: <decisions waiting for the user>

## Next
1. **<feature>** — <goal in one line>. Spec: `specs/<feature>/` | none yet. <Why now / depends on>
2. …

## Later
- **<feature>** — <goal>. <What would bring it forward>

## To confirm with the user
- <question> — <where it came from, what is implemented meanwhile>
```

Rules:
- One item is a feature: something one branch, one spec folder and one changelog entry carry.
  Too big for that → split it; too small → fold it into another item.
- "Now" holds at most one feature per checkout. It is kept current at each step's commit, so a
  session that ends anywhere can resume from it alone.
- Done items leave the roadmap; the changelog keeps them.
- Every item says why it is where it is; a "Later" item ranked by today's size or speed says
  what it grows with (`/perf`).

## Actions
- **show** — Now, then the top of Next, briefly.
- **add** — place the item with the user (`AskUserQuestion` when the order is not obvious).
- **refine / reorder** — rewrite goals or order from what was learned; say what changed and why.
- **start <item>** — the item goes to Now:
  1. from an up-to-date `main` with a clean tree: `git switch -c feature/<item>`;
  2. save a benchmark baseline on that commit when the project has a Bench setting;
  3. create `specs/<item>/` and hand over to `/bdd` (an existing folder: the spec is updated);
  4. write Now, commit `ROADMAP.md` on the branch.
- **now** — update the Now block (called by `/feature-workflow` at each commit).
