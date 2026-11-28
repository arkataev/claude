# CI review pilot

A trial of the flow's review on GitHub Actions. Nothing here changes the flow the projects use
today: this lives on the branch `feature/flow-ci-pilot`, and the installed flow is `main`.

## What it does
A comment `/review specs/<feature>/stepN-brief.md [lens,lens,...]` on a PR, by the repo's owner, starts it:

1. `prepare` reads the brief path from the comment, pins the PR's head commit and says on the PR
   that the review started.
2. `lens` runs once per lens (`tests`, `correctness`, `design`), in parallel. Each job checks out
   the PR, installs the project and this flow into `~/.claude`, and resets the PR's commits so the
   change is uncommitted (the `reviewer` agent reviews `git diff`). Then it runs the unchanged
   `reviewer` agent with the lens as a note (`ci/lenses/`), and gets the findings back as JSON
   (`ci/findings.schema.json`).
3. `merge` puts findings of different lenses within 3 lines of each other together as one finding.
   It counts how many lenses agree, posts one PR review (a finding on a changed line is an inline
   comment), and keeps `findings.json` for 90 days.

## Setting it up for a project
- The project calls `review.yml` from its own workflow (see the sandbox `flow-pilot`).
- Secret `CLAUDE_CODE_OAUTH_TOKEN`: the output of `claude setup-token` (the subscription).
  `ANTHROPIC_API_KEY` must not be set in these jobs, or it wins over the token.
- While this repo is private: in its Settings, Actions, General, "Access", allow the user's own
  repositories, and give the project a secret `FLOW_REPO_TOKEN`. That secret is a fine-grained
  token with "Contents: read" on this repo only.

## The step scorecard
One PR per step (the user, 2026-11-27): a step's PR has the feature branch as its base, and the
feature's PR to `main` holds no unreviewed code. `scorecard.yml`, called on every `pull_request`
event, runs three deterministic checks (no model, seconds) and keeps one PR comment and one
status:

- **size** (`ci/pr_size.py`): only source lines count, a warning over 400 (label `large`) and a
  failure over 800; tests are reported, never capped, so writing fewer tests is never a way to fit.
  The cap prompts a choice, never a squeeze: split at a natural seam, or add the label
  `size-exempt` and a line `Size exempt: <reason>` to the PR description.
- **scenarios** (`ci/scenarios.py`): a test cites its scenario (`Scenario: <name>.` in its
  docstring, or pytest-bdd). It fails on a citation of no scenario, a citation the PR dropped, a
  scenario added with no test, and, on the feature's PR into the default branch, any scenario of
  that feature (`specs/<feature>/`, from the branch `feature/<feature>`) with no test.
- **interface** (`ci/interface.py`): the top-level names of the public modules (no `_` in the
  path), compared with the base by `ast`. Any change fails unless the PR description has
  `Interface change: <spec folder>` and every changed name appears in a Markdown file there.

- **gate** (`ci/run_gate.py`): the project's own gate command (`make -k test` by default, so a
  fix round sees every failing step at once), run once on a clean checkout. The flow runs no
  linter of its own: the project's config decides, locally and in CI alike. With
  `RUFF_OUTPUT_FORMAT=github`, Ruff marks its findings on the PR's lines.

`/review` runs the same gate once before any reviewer. If it fails, the review is skipped with a
comment that shows why; if it passes, the reviewers get its result and do not run it again (the
review skills already say "run it unless the caller just did").

## The flow that uses it
`/solid-workflow-ci` and its agents `solid-critic-ci`, `solid-writer-ci` and `solid-reviewer-ci`
are copies of `/solid-workflow` and its agents; the originals do not change (the user's rule for
workflow trials). What the copies add:
- the plan marks each step small, medium or large (no line counts), names a large step's natural
  seam, and lists the public names each step adds, changes or removes; the critic checks both;
- each step is a branch `step/<name>/<N>` and a PR into `feature/<name>` (a branch
  `feature/<name>/stepN` cannot exist beside `feature/<name>` in git);
- the brief states the size budget and the Interface list; the writer stops at the budget instead
  of squeezing the code, and changes no public name the list does not name;
- the review runs in CI on `/review`; triage verdicts are replies on the review's comments;
- the reviewer spends no findings on what the scorecard checks, and has one more finding type:
  code squeezed to fit the size budget.

The copies live on this branch only, so no project's installed flow has them; trying the flow
locally needs them installed (merging just these new files into `main` changes no existing flow).

Gotcha: a pull_request run uses the workflow file of the PR's test merge with its base. A PR
opened before the caller workflow reached the base gets no run, even when edited, until its
branch is updated from the base.

## What the pilot measures
- Recall per lens against the sandbox's planted defects (the answer key is kept outside every
  repo the runners see).
- Precision: the findings you would reject.
- Agreement: is a finding that 2 or 3 lenses report more often right?
- Cost (`total_cost_usd`), turns and time per lens, and the subscription's usage after a run.
- What breaks: anything the CI run does differently from a local review.

## Learned so far
- Run 1 (`reviewer`, 3 lenses, the toy PR): all 4 planted and 4 unplanted defects found, no false
  alarm, 1.5 minutes, about $0.79 API-equivalent (on a subscription, usage, not a charge).
- `claude -p --agent X` runs X as the main session, and there its `skills:` are only listed, not
  loaded as they are for a subagent. Run 1 had no skill text. `run_lens.py` now reads the agent's
  `skills:` and `effort:` and passes them itself (`--append-system-prompt`, `--effort`).
- Grouping findings by line distance joins different defects and splits one defect across the
  code and its test. Grouping by root cause needs a model step.
- The lenses strayed into each other's areas. Whether they beat one whole reviewer is the
  question of run 2: `/review <brief>` (3 lenses) against `/review <brief> whole`.

- Run 3 (the gate before the reviewers): the CI gate takes 2 to 3 s on the sandbox; the whole
  reviewer reported "passed in CI … not re-run" and cost $0.30 API-equivalent against $0.50 in
  run 2 (one sample each). A red gate skipped the review with a comment; Ruff's finding showed on
  its line through `RUFF_OUTPUT_FORMAT=github`.
- A job's `permissions:` are its whole grant: listing a PR's files needs `pull-requests: read`,
  and a 403 piped into a script reads as data unless the step sets `pipefail`.

- Run 4 (the scorecard's rows in the reviewer's prompt): `solid-reviewer-ci` dropped the finding
  the scorecard reports ("already reports that, so it is not counted again") and kept the two no
  script sees: a citing test that does not test its scenario, and the case bug. Told only that a
  scorecard exists, it had reported the missing citations again.

- Run 5 (the sandbox's loans step 1, the first end-to-end PR): the scorecard's interface row
  flagged a public `SCHEMA` the plan had not named; the designer made it private and the plan
  names the removal, all before any review. The review itself never ran: the repo's token was
  refused (`401 Invalid bearer token`), and the run went green with "0 findings". A refused login
  still prints a JSON result (`is_error: true`), so "the JSON parsed" is not "the reviewer
  reviewed". Now a lens without a review is named in the review's title and fails the run.
  Rerun with a good token: 4 findings, no row of the scorecard repeated, $1.09 API-equivalent,
  2.5 minutes. The one gap (F1, `main.py`'s local date: no test sees it, 85 of 85 pass with it
  replaced) was proved by a mutant in a throwaway copy, with a control mutant to show the copy
  ran its own source. The three nits are on the tests' claims (a fault loop that could run zero
  times, citations of Acceptance lines the spec lacks, a name that says more than the test checks).

## The end-to-end sandbox
`arkataev/flow-sandbox` (private, `~/dev/flow-sandbox`): a lending library in the solid shape,
with a done feature (catalog) and one on the roadmap (loans: borrowing, a race for the last copy,
an overdue list with a statement budget, interface changes). It is for running a real feature
through `/solid-workflow-ci` from spec to merge. Its `.claude/` links the copies from this
worktree (git-ignored), so a session started in the sandbox has them and no installed flow
changes.

## Open questions the pilot answers
- Does `--max-budget-usd` stop a run under a subscription token?
- Does a lens keep to its focus, or does each one do the whole review?
- Is a mixed reset to the merge base a good stand-in for "the uncommitted diff"?

## Not in the pilot yet
`/step` (the writer in CI), `/fix`, saving your replies as the triage, lessons, evals, tags.
