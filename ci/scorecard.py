"""Merge the step checks' results into one PR comment and one verdict.

Each check writes a result file: {"check", "state", "headline", "details"}, with the state one of
pass, warn, exempt or fail. The scorecard fails when any check fails.
"""

import argparse
import json
import sys
from pathlib import Path

MARKER = "<!-- flow-scorecard -->"
ORDER = ("gate", "size", "scenarios", "interface")
MARK = {"pass": "✅", "exempt": "☑️", "warn": "⚠️", "fail": "❌"}


def overall(results: list[dict[str, str]]) -> str:
    """The worst state of the checks."""
    states = {result["state"] for result in results}
    return next((state for state in ("fail", "warn", "exempt") if state in states), "pass")


def comment(results: list[dict[str, str]]) -> str:
    """The scorecard: one row per check, then each check's details."""
    rows = [f"| {r['check']} | {MARK.get(r['state'], '?')} {r['state']} | {r['headline']} |" for r in results]
    parts = [MARKER, f"### Step scorecard: {overall(results)}", "", "| check | state | result |", "|---|---|---|", *rows]
    for result in results:
        if result["details"]:
            opened = " open" if result["state"] == "fail" else ""
            parts += ["", f"<details{opened}><summary>{result['check']}</summary>", "", result["details"], "", "</details>"]
    return "\n".join(parts) + "\n"


def summary(results: list[dict[str, str]]) -> str:
    """The rows as plain text for a reviewer's prompt, with the details of every row that did not pass."""
    lines = [f"- {r['check']}: {r['state']}: {r['headline']}" for r in results]
    for result in results:
        if result["state"] != "pass" and result["details"]:
            lines += ["", f"{result['check']}, in detail:", result["details"]]
    return "\n".join(lines) + "\n"


def main() -> int:
    """Write the comment, the reviewer's summary and the overall state."""
    args = _arguments()
    results = [json.loads(path.read_text()) for path in Path(args.results).glob("*.json")]
    results.sort(key=lambda r: ORDER.index(r["check"]) if r["check"] in ORDER else len(ORDER))
    Path(args.comment).write_text(comment(results))
    if args.summary:
        Path(args.summary).write_text(summary(results))
    Path(args.state).write_text(overall(results))
    print(f"scorecard: {overall(results)}")
    return 0


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", required=True, help="the folder of the checks' result files")
    parser.add_argument("--comment", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--summary", help="also write the rows as plain text for a reviewer")
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
