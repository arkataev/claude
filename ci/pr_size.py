"""Count a PR's changed lines by kind, and hold its source lines to a cap.

Only source lines count toward the cap. Test lines are reported but never capped, so that writing
fewer tests is never a way to fit; other files (specs, docs) are reported; ignored files
(generated, lock files) are left out. The cap prompts a choice, split or exempt, never a squeeze.

Patterns are fnmatch patterns, where `*` also crosses folders: `src/*` is everything under `src/`.
The first match wins, in the order ignored, tests, source; a file that matches none is "other".
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from enum import StrEnum
from fnmatch import fnmatch
from pathlib import Path

EXEMPT_LABEL = "size-exempt"
EXEMPT_REASON = re.compile(r"^[ \t]*size exempt:[ \t]*(\S.*)$", re.IGNORECASE | re.MULTILINE)


class Kind(StrEnum):
    """What a changed file is, for the count."""

    SOURCE = "source"
    TESTS = "tests"
    OTHER = "other"
    IGNORED = "ignored"


class State(StrEnum):
    """The check's outcome."""

    PASS = "pass"
    WARN = "warn"
    EXEMPT = "exempt"
    FAIL = "fail"


@dataclass(frozen=True)
class Patterns:
    """The project's globs for each counted kind."""

    source: tuple[str, ...]
    tests: tuple[str, ...]
    ignored: tuple[str, ...]

    def kind_of(self, path: str) -> Kind:
        """The kind of one changed file."""
        for kind, globs in ((Kind.IGNORED, self.ignored), (Kind.TESTS, self.tests), (Kind.SOURCE, self.source)):
            if any(fnmatch(path, glob) for glob in globs):
                return kind
        return Kind.OTHER


@dataclass(frozen=True)
class Tally:
    """Changed lines (added plus deleted) and files of one kind."""

    lines: int
    files: int


@dataclass(frozen=True)
class Verdict:
    """The check's outcome, with what to do about it."""

    state: State
    message: str


def tally(files: list[dict[str, object]], patterns: Patterns) -> dict[Kind, Tally]:
    """Sum the changed lines per kind from the GitHub API's list of a PR's files."""
    lines = dict.fromkeys(Kind, 0)
    counts = dict.fromkeys(Kind, 0)
    for changed in files:
        kind = patterns.kind_of(str(changed["filename"]))
        lines[kind] += int(str(changed["additions"])) + int(str(changed["deletions"]))
        counts[kind] += 1
    return {kind: Tally(lines[kind], counts[kind]) for kind in Kind}


def judge(source_lines: int, warn: int, fail: int, labels: list[str], body: str) -> Verdict:
    """Judge the source lines against the thresholds and the exemption."""
    if source_lines <= warn:
        return Verdict(State.PASS, f"{source_lines} source lines, within {warn}.")
    if EXEMPT_LABEL in labels:
        reason = EXEMPT_REASON.search(body)
        if reason:
            return Verdict(State.EXEMPT, f"{source_lines} source lines, exempt: {reason.group(1).strip()}")
        return Verdict(
            State.FAIL,
            f"The PR has the `{EXEMPT_LABEL}` label but no reason: add a line "
            "`Size exempt: <reason>` to the PR description.",
        )
    if source_lines <= fail:
        return Verdict(
            State.WARN,
            f"{source_lines} source lines, over the warning at {warn}. Look for a natural seam before "
            "the next step grows it.",
        )
    return Verdict(
        State.FAIL,
        f"{source_lines} source lines, over the cap of {fail}. Split the step at a natural seam, where "
        "each part still adds behavior and passes its scenarios. If the step is one slice that cannot "
        f"be split, add the label `{EXEMPT_LABEL}` and a line `Size exempt: <reason>` to the PR "
        "description. Do not compress the code to fit.",
    )


def details(tallies: dict[Kind, Tally], warn: int, fail: int) -> str:
    """The counts per kind, for the scorecard's details."""
    source, tests = tallies[Kind.SOURCE], tallies[Kind.TESTS]
    ratio = f"{tests.lines / source.lines:.1f}" if source.lines else "–"
    rows = [f"| {kind} | {tallies[kind].lines} | {tallies[kind].files} |" for kind in Kind]
    return "\n".join(
        [
            "| kind | lines changed | files |",
            "|---|---|---|",
            *rows,
            "",
            f"Test lines per source line: {ratio}. Only source lines count: warning over {warn}, cap {fail}.",
        ]
    )


def main() -> int:
    """Write the check's result for the scorecard."""
    args = _arguments()
    patterns = Patterns(_globs(args.source), _globs(args.tests), _globs(args.ignored))
    files = json.loads(Path(args.files).read_text())
    tallies = tally(files, patterns)
    labels = [label for label in args.labels.split(",") if label]
    verdict = judge(tallies[Kind.SOURCE].lines, args.warn, args.fail, labels, Path(args.body).read_text())
    result = {
        "check": "size",
        "state": verdict.state,
        "headline": verdict.message,
        "details": details(tallies, args.warn, args.fail),
        **{f"{kind}_lines": tallies[kind].lines for kind in Kind},
    }
    Path(args.result).write_text(json.dumps(result))
    print(f"{verdict.state}: {verdict.message}")
    return 0


def _globs(text: str) -> tuple[str, ...]:
    return tuple(glob.strip() for glob in text.split(",") if glob.strip())


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", required=True, help="the API's list of the PR's files, as JSON")
    parser.add_argument("--labels", default="", help="the PR's labels, comma-separated")
    parser.add_argument("--body", required=True, help="a file holding the PR's description")
    parser.add_argument("--source", required=True)
    parser.add_argument("--tests", required=True)
    parser.add_argument("--ignored", default="")
    parser.add_argument("--warn", type=int, default=400)
    parser.add_argument("--fail", type=int, default=800)
    parser.add_argument("--result", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
