#!/usr/bin/env bash
# Run the step scorecard's checks (size, scenarios, interface) on a PR, one result file each.
# scorecard.yml and review.yml both call it, so the reviewer sees the rows the PR shows. Everything
# about the PR comes from the API, so a pull_request run and a /review comment read the same facts.
#
# Environment: HEAD_DIR (a full-history checkout of the PR's head), OUT (the results folder), REPO,
# PR, SOURCE, TESTS; optional IGNORED, WARN, FAIL.
set -euo pipefail

flow="$(cd "$(dirname "$0")/.." && pwd)"
work="$(mktemp -d)"
mkdir -p "$OUT"

gh api "repos/$REPO/pulls/$PR" > "$work/pr.json"
field() { python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print($1)" "$work/pr.json"; }
python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["body"] or "", end="")' "$work/pr.json" > "$work/body.txt"
labels="$(field '",".join(label["name"] for label in d["labels"])')"
head_branch="$(field 'd["head"]["ref"]')"
base_ref="$(field 'd["base"]["ref"]')"
default_branch="$(field 'd["base"]["repo"]["default_branch"]')"
base_sha="$(field 'd["base"]["sha"]')"

gh api --paginate --slurp "repos/$REPO/pulls/$PR/files" \
  | python3 -c 'import json,sys; print(json.dumps([f for page in json.load(sys.stdin) for f in page]))' > "$work/files.json"
git -C "$HEAD_DIR" worktree add --detach "$work/base" "$(git -C "$HEAD_DIR" merge-base "$base_sha" HEAD)" > /dev/null

python3 "$flow/ci/pr_size.py" --files "$work/files.json" --labels "$labels" --body "$work/body.txt" \
  --source "$SOURCE" --tests "$TESTS" --ignored "${IGNORED:-}" --warn "${WARN:-400}" --fail "${FAIL:-800}" \
  --result "$OUT/size.json"
final=()
[ "$base_ref" = "$default_branch" ] && final=(--final)
python3 "$flow/ci/scenarios.py" --root "$HEAD_DIR" --base-root "$work/base" --tests "$TESTS" \
  --branch "$head_branch" "${final[@]}" --result "$OUT/scenarios.json"
python3 "$flow/ci/interface.py" --root "$HEAD_DIR" --base-root "$work/base" --source "$SOURCE" \
  --tests "$TESTS" --body "$work/body.txt" --result "$OUT/interface.json"

git -C "$HEAD_DIR" worktree remove --force "$work/base"
