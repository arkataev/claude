"""Merge the lens results of one PR into one findings file and one GitHub review payload.

Findings of different lenses on the same file within a few lines are one finding; the number of
lenses that report it is its agreement. A finding on a changed line becomes an inline comment;
the others go in the review's body, since GitHub refuses a comment on a line outside the diff.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

NEAR_LINES = 3
SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
BODY_LIMIT = 60_000


def main() -> int:
    """Write findings.json and review.json from the lens result files."""
    args = _arguments()
    lenses = [json.loads(path.read_text()) for path in sorted(Path(args.lenses).glob("*.json"))]
    groups = _group([finding for lens in lenses for finding in _findings_of(lens)])
    answered = sum(1 for lens in lenses if _structured(lens))
    findings = [_merged(index, group, answered) for index, group in enumerate(groups, start=1)]
    changed = changed_lines(Path(args.diff).read_text())
    summary = {"pr": args.pr, "commit": args.commit, "lenses": [_lens_summary(lens) for lens in lenses], "findings": findings}
    Path(args.out).write_text(json.dumps(summary, indent=2))
    Path(args.review).write_text(json.dumps(_review(summary, changed, lenses)))
    print(f"{len(lenses)} lenses, {len(findings)} findings")
    return 0


def changed_lines(diff: str) -> dict[str, set[int]]:
    """Return, per file, the new-side line numbers a review comment may point at."""
    lines: dict[str, set[int]] = {}
    path: str | None = None
    number = 0
    in_hunk = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path, in_hunk = None, False
        elif not in_hunk and line.startswith("+++ "):
            target = line[4:]
            path = None if target == "/dev/null" else target.removeprefix("b/")
            if path:
                lines.setdefault(path, set())
        elif match := HUNK.match(line):
            number, in_hunk = int(match.group(1)), True
        elif in_hunk and path and line[:1] in {" ", "+"}:
            lines[path].add(number)
            number += 1
    return lines


def _structured(lens: dict[str, Any]) -> dict[str, Any]:
    return (lens.get("claude") or {}).get("structured_output") or {}


def _findings_of(lens: dict[str, Any]) -> list[dict[str, Any]]:
    structured = _structured(lens)
    return [{**finding, "lens": lens["lens"]} for finding in structured.get("findings", [])]


def _group(findings: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    for finding in sorted(findings, key=lambda f: (f["file"], f["line"])):
        home = next((group for group in groups if _same_place(group[0], finding)), None)
        if home is None:
            groups.append([finding])
        else:
            home.append(finding)
    return sorted(groups, key=lambda group: (min(SEVERITY_RANK[f["severity"]] for f in group), -len(group)))


def _same_place(first: dict[str, Any], other: dict[str, Any]) -> bool:
    if first["file"] != other["file"]:
        return False
    if first["line"] == 0 or other["line"] == 0:
        return first["line"] == other["line"] and first["rule"] == other["rule"]
    return abs(first["line"] - other["line"]) <= NEAR_LINES


def _merged(index: int, group: list[dict[str, Any]], lens_count: int) -> dict[str, Any]:
    lead = min(group, key=lambda f: SEVERITY_RANK[f["severity"]])
    lenses = sorted({finding["lens"] for finding in group})
    return {
        "id": f"F{index}",
        **{key: lead[key] for key in ("file", "line", "kind", "severity", "rule", "summary", "failure", "fix", "verified")},
        "lenses": lenses,
        "agreement": f"{len(lenses)}/{lens_count}",
        "also": [{"lens": f["lens"], "summary": f["summary"]} for f in group if f is not lead],
        "verdict": None,
    }


def _lens_summary(lens: dict[str, Any]) -> dict[str, Any]:
    claude = lens.get("claude") or {}
    structured = claude.get("structured_output") or {}
    return {
        "lens": lens["lens"],
        "ok": bool(structured),
        "error": lens.get("error") or (None if structured else "no structured output"),
        "gate": structured.get("gate"),
        "findings": len(structured.get("findings", [])),
        "cost_usd": claude.get("total_cost_usd"),
        "turns": claude.get("num_turns"),
        "duration_s": lens.get("duration_s"),
    }


def _review(summary: dict[str, Any], changed: dict[str, set[int]], lenses: list[dict[str, Any]]) -> dict[str, Any]:
    inline = [f for f in summary["findings"] if f["line"] in changed.get(f["file"], set())]
    elsewhere = [f for f in summary["findings"] if f not in inline]
    comments = [{"path": f["file"], "line": f["line"], "side": "RIGHT", "body": _comment(f)} for f in inline]
    return {"commit_id": summary["commit"], "event": "COMMENT", "body": _body(summary, elsewhere, lenses), "comments": comments}


def _comment(finding: dict[str, Any]) -> str:
    lines = [
        f"**{finding['id']}** · {finding['kind']} · {finding['severity']} · {finding['agreement']} lenses ({', '.join(finding['lenses'])})",
        "",
        finding["summary"],
        "",
        f"**Fails when:** {finding['failure']}",
        f"**Fix:** {finding['fix']}",
        f"**Rule:** {finding['rule']} · {finding['verified'].replace('_', ' ')}",
    ]
    lines += [f"> *{other['lens']}:* {other['summary']}" for other in finding["also"]]
    return "\n".join(lines)


def _body(summary: dict[str, Any], elsewhere: list[dict[str, Any]], lenses: list[dict[str, Any]]) -> str:
    rows = [
        f"| {lens['lens']} | {_gate(lens['gate'])} | {lens['findings']} | {_money(lens['cost_usd'])} | {lens['duration_s']} s | {lens['error'] or ''} |"
        for lens in summary["lenses"]
    ]
    parts = [
        f"### Flow review (pilot): {len(summary['findings'])} findings from {len(summary['lenses'])} lenses",
        "",
        "| lens | gate | findings | cost | time | error |",
        "|---|---|---|---|---|---|",
        *rows,
        "",
        "Reply on a finding with `accept` or `reject: <reason>`.",
    ]
    if elsewhere:
        parts += ["", "**Findings not on a changed line**", ""]
        parts += [f"- **{f['id']}** · {f['kind']} · {f['severity']} · `{f['file']}:{f['line']}`: {f['summary']} ({f['agreement']})" for f in elsewhere]
    for lens in lenses:
        report = _structured(lens).get("report", "")
        if not report:
            continue
        parts += ["", f"<details><summary>{lens['lens']} report</summary>", "", "```", report, "```", "</details>"]
    return "\n".join(parts)[:BODY_LIMIT]


def _gate(gate: dict[str, Any] | None) -> str:
    if gate is None:
        return "?"
    return ("pass" if gate["passed"] else "FAIL") + f": {gate['summary']}"


def _money(cost: float | None) -> str:
    return "?" if cost is None else f"${cost:.2f}"


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lenses", required=True, help="folder of lens result files")
    parser.add_argument("--diff", required=True)
    parser.add_argument("--pr", required=True, type=int)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--review", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
