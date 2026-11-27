"""Run the reviewer agent with one lens on the working-tree change and save its structured result.

The change under review must already be uncommitted (the workflow resets the PR's commits onto
their merge base), because the reviewer agent reviews `git diff` plus the untracked files.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PROMPT = """Review the change for the brief {brief}.

{lens}
This is a CI run on a pull request. The change under review is the working-tree diff against the
PR's base (`git diff` plus the untracked files in `git status`). There is no designer to ask and
no follow-up message: give your whole review in this one answer. Your final answer must match the
JSON schema: put the review skill's report in "report", and every finding of the report also as
one item of "findings".
"""

TIMEOUT_SECONDS = 25 * 60


def main() -> int:
    """Run one lens and write its result file; a failed run is recorded, not raised."""
    args = _arguments()
    flow = Path(args.flow)
    prompt = PROMPT.format(brief=args.brief, lens=(flow / "ci/lenses" / f"{args.lens}.md").read_text())
    command = [
        "claude",
        "-p",
        "--agent",
        "reviewer",
        "--output-format",
        "json",
        "--json-schema",
        (flow / "ci/findings.schema.json").read_text(),
        "--allowedTools",
        "Read,Grep,Glob,Bash",
        "--max-budget-usd",
        args.budget,
    ]
    started = time.monotonic()
    result = _run(command, prompt)
    result["lens"] = args.lens
    result["duration_s"] = round(time.monotonic() - started, 1)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2))
    claude = result.get("claude") or {}
    print(f"lens {args.lens}: exit {result['exit_code']}, structured={claude.get('structured_output') is not None}")
    return 0


def _run(command: list[str], prompt: str) -> dict[str, object]:
    # The prompt goes through stdin so no variadic flag can swallow it.
    try:
        process = subprocess.run(command, input=prompt, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return {"exit_code": None, "error": f"timed out after {TIMEOUT_SECONDS} s", "claude": None}
    try:
        claude = json.loads(process.stdout)
    except json.JSONDecodeError:
        claude = None
    return {
        "exit_code": process.returncode,
        "error": None if claude else "no JSON on stdout",
        "stderr_tail": process.stderr[-2000:],
        "claude": claude,
    }


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lens", required=True)
    parser.add_argument("--brief", required=True)
    parser.add_argument("--flow", required=True, help="the flow checkout")
    parser.add_argument("--out", required=True)
    parser.add_argument("--budget", default="3")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
