# CI review pilot

A trial of the flow's review on GitHub Actions. Nothing here changes the flow the projects use
today: this lives on the branch `feature/flow-ci-pilot`, and the installed flow is `main`.

## What it does
A comment `/review specs/<feature>/stepN-brief.md` on a PR, by the repo's owner, starts it:

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

## What the pilot measures
- Recall per lens against the sandbox's planted defects (the answer key is kept outside every
  repo the runners see).
- Precision: the findings you would reject.
- Agreement: is a finding that 2 or 3 lenses report more often right?
- Cost (`total_cost_usd`), turns and time per lens, and the subscription's usage after a run.
- What breaks: anything the CI run does differently from a local review.

## Open questions the pilot answers
- Does `claude -p --agent reviewer` load the agent's preloaded skills (`review`, `mutants`)?
- Does `--max-budget-usd` stop a run under a subscription token?
- Does a lens keep to its focus, or does each one do the whole review?
- Is a mixed reset to the merge base a good stand-in for "the uncommitted diff"?

## Not in the pilot yet
`/step` (the writer in CI), `/fix`, saving your replies as the triage, lessons, evals, tags.
