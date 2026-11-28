"""Run a reviewer agent with one lens on the working-tree change and save its structured result.

The change under review must already be uncommitted (the workflow resets the PR's commits onto
their merge base), because the reviewer agents review `git diff` plus the untracked files.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROMPT = """Review the change for the brief {brief}.

{lens}
The caller ran the gate and the step scorecard in CI just now, on this same commit:

{scorecard}
Do not run the gate again; report its row as the gate's result. Every row is already on the PR:
do not report again what a row reports (a scenario with no citing test, the size, a public name).
Spend your findings on what no script sees, such as whether a citing test really checks its
scenario.

This is a CI run on a pull request. The change under review is the working-tree diff against the
PR's base (`git diff` plus the untracked files in `git status`). There is no designer to ask and
no follow-up message: give your whole review in this one answer. Your final answer must match the
JSON schema: put the review skill's report in "report", and every finding of the report also as
one item of "findings".
"""

# `--agent` runs the agent as the main session, where its `skills:` are only listed, not loaded
# as they are for a subagent; their text goes in the system prompt so CI reviews as locally.
PRELOAD = """The following skills are preloaded for you, in full, as they are when you run as a
subagent. Follow them as your own instructions.

{skills}
"""

TIMEOUT_SECONDS = 25 * 60


def main() -> int:
    """Run one lens and write its result file; a failed run is recorded, not raised."""
    args = _arguments()
    flow, home = Path(args.flow), Path(args.claude_home)
    agent = AgentFile.read(home / "agents" / f"{args.agent}.md")
    skills = {name: (home / "skills" / name / "SKILL.md").read_text() for name in agent.skills}
    prompt = PROMPT.format(brief=args.brief, scorecard=Path(args.scorecard).read_text(), lens=(flow / "ci/lenses" / f"{args.lens}.md").read_text())
    command = review_command(args.agent, agent, skills, (flow / "ci/findings.schema.json").read_text(), args.budget)
    started = time.monotonic()
    result = _run(command, prompt)
    result |= {
        "lens": args.lens,
        "agent": args.agent,
        "effort": agent.effort,
        "preloaded": {name: len(text) for name, text in skills.items()},
        "duration_s": round(time.monotonic() - started, 1),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2))
    claude = result.get("claude") or {}
    print(f"lens {args.lens}: exit {result['exit_code']}, preloaded {list(skills)}, structured={claude.get('structured_output') is not None}")
    return 0


class AgentFile:
    """The parts of an agent file's front matter a headless run must apply itself."""

    def __init__(self, skills: list[str], effort: str | None) -> None:
        self.skills = skills
        self.effort = effort

    @classmethod
    def read(cls, path: Path) -> "AgentFile":
        """Read `skills:` (a YAML list) and `effort:` from the front matter of an agent file."""
        lines = path.read_text().split("\n---", 1)[0].splitlines()
        skills: list[str] = []
        effort = None
        in_skills = False
        for line in lines:
            if line.startswith("skills:"):
                in_skills = True
            elif in_skills and line.startswith("  - "):
                skills.append(line.removeprefix("  - ").strip())
            else:
                in_skills = False
                if line.startswith("effort:"):
                    effort = line.removeprefix("effort:").strip()
        return cls(skills, effort)


def review_command(name: str, agent: AgentFile, skills: dict[str, str], schema: str, budget: str) -> list[str]:
    """The headless command that runs the agent with its skills and effort applied."""
    preload = PRELOAD.format(skills="\n\n".join(f'<skill name="{n}">\n{text}\n</skill>' for n, text in skills.items()))
    command = ["claude", "-p", "--agent", name, "--append-system-prompt", preload]
    if agent.effort:
        command += ["--effort", agent.effort]
    return command + [
        "--output-format",
        "json",
        "--json-schema",
        schema,
        "--allowedTools",
        "Read,Grep,Glob,Bash",
        "--max-budget-usd",
        budget,
    ]


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
        "error": failure(process.returncode, claude),
        "stderr_tail": process.stderr[-2000:],
        "claude": claude,
    }


def failure(exit_code: int, claude: dict[str, Any] | None) -> str | None:
    """Why the run gave no review, or None when it gave one.

    A refused login still prints a JSON result, with `is_error` and the API's message, so a parsed
    result is not by itself a review.
    """
    if claude is None:
        return f"no JSON on stdout (exit {exit_code})"
    if claude.get("is_error"):
        return f"claude: {str(claude.get('result') or claude.get('subtype'))[:300]}"
    if exit_code != 0:
        return f"exit {exit_code}"
    if not claude.get("structured_output"):
        return "no structured output"
    return None


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lens", required=True)
    parser.add_argument("--brief", required=True)
    parser.add_argument("--agent", default="reviewer")
    parser.add_argument("--flow", required=True, help="the flow checkout")
    parser.add_argument("--claude-home", default=str(Path.home() / ".claude"))
    parser.add_argument("--out", required=True)
    parser.add_argument("--budget", default="3")
    parser.add_argument("--scorecard", required=True, help="the scorecard's rows, as the CI ran them")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
