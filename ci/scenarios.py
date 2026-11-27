"""Check that the tests cite the spec's scenarios, against the PR's base.

A scenario is cited by a test docstring line `Scenario: <exact name>.`, by pytest-bdd's
`@scenario("<file>", "<name>")`, or by `scenarios("<file>")`, which binds every scenario of a file.
A scenario tagged `@documented-only` needs no test.

It fails on a citation of a scenario that does not exist, a citation the base had and the PR
dropped, and a scenario the PR adds with no test. On the feature's PR into the default branch it
also fails on any scenario of that feature (`specs/<feature>/`, the name from the branch
`feature/<feature>`) with no test.
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

SCENARIO = re.compile(r"^\s*(?:Scenario|Scenario Outline|Scenario Template|Example):\s*(.+?)\s*$")
DOCSTRING_CITATION = re.compile(r"""^\s*(?:[rRuU]?(?:\"\"\"|'''))?\s*Scenario:\s*(.+?)\.?\s*(?:\"\"\"|''')?\s*$""")
BDD_SCENARIO = re.compile(r"""@scenario\(\s*["']([^"']+)["']\s*,\s*["']([^"']+)["']""")
BDD_SCENARIOS = re.compile(r"""\bscenarios\(([^)]*)\)""")
QUOTED = re.compile(r"""["']([^"']+)["']""")
DOCUMENTED_ONLY = "@documented-only"


@dataclass(frozen=True)
class Scenario:
    """One scenario of a feature file."""

    name: str
    feature: str
    documented_only: bool


@dataclass(frozen=True)
class Tree:
    """The scenarios and the citations of one checkout."""

    scenarios: tuple[Scenario, ...]
    citations: frozenset[str]

    @classmethod
    def scan(cls, root: Path, tests: tuple[str, ...]) -> "Tree":
        """Read every feature file and every test file under root."""
        scenarios: list[Scenario] = []
        cited: set[str] = set()
        bound_files: list[str] = []
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            if _skipped(relative) or not path.is_file():
                continue
            if path.suffix == ".feature":
                scenarios += scenarios_in(path.read_text(), relative)
            elif path.suffix == ".py" and any(fnmatch(relative, glob) for glob in tests):
                names, files = citations_in(path.read_text())
                cited |= names
                bound_files += files
        for scenario in scenarios:
            if any(scenario.feature.endswith(bound.lstrip("./")) for bound in bound_files):
                cited.add(scenario.name)
        return cls(tuple(scenarios), frozenset(cited))

    def names(self) -> set[str]:
        """The names of all scenarios."""
        return {scenario.name for scenario in self.scenarios}

    def uncited(self, scenarios: tuple[Scenario, ...] | None = None) -> set[str]:
        """The scenarios that need a test and have none."""
        return {s.name for s in (scenarios or self.scenarios) if not s.documented_only and s.name not in self.citations}


@dataclass(frozen=True)
class Outcome:
    """What the check found."""

    stale: set[str]
    lost: set[str]
    added_untested: set[str]
    feature_untested: set[str]
    feature: str | None
    feature_total: int

    @property
    def failed(self) -> bool:
        """Whether any finding fails the check."""
        return bool(self.stale or self.lost or self.added_untested or self.feature_untested)


def scenarios_in(text: str, feature: str) -> list[Scenario]:
    """The scenarios of one feature file, with their tags."""
    found: list[Scenario] = []
    tags: set[str] = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("@"):
            tags |= set(stripped.split())
        elif match := SCENARIO.match(line):
            found.append(Scenario(match.group(1), feature, DOCUMENTED_ONLY in tags))
            tags = set()
        elif stripped and not stripped.startswith("#"):
            tags = set()
    return found


def citations_in(text: str) -> tuple[set[str], list[str]]:
    """The scenario names one test file cites, and the feature files it binds whole."""
    names = {match.group(1) for line in text.splitlines() if (match := DOCSTRING_CITATION.match(line))}
    names |= {match.group(2) for match in BDD_SCENARIO.finditer(text)}
    files = [quoted for call in BDD_SCENARIOS.finditer(text) for quoted in QUOTED.findall(call.group(1))]
    return names, files


def judge(head: Tree, base: Tree, feature: str | None, final: bool) -> Outcome:
    """Compare the PR's tree with its base."""
    head_names = head.names()
    in_feature = tuple(s for s in head.scenarios if feature and f"specs/{feature}/" in s.feature)
    return Outcome(
        stale=set(head.citations) - head_names,
        lost=(set(base.citations) & base.names() & head_names) - set(head.citations),
        added_untested=head.uncited() - base.names(),
        feature_untested=head.uncited(in_feature) if final and in_feature else set(),
        feature=feature,
        feature_total=len(in_feature),
    )


def headline(outcome: Outcome, head: Tree) -> str:
    """One line for the scorecard."""
    if not outcome.failed:
        total = sum(1 for s in head.scenarios if not s.documented_only)
        return f"{total - len(head.uncited())} of {total} scenarios cited; nothing lost or stale"
    parts = []
    if outcome.feature_untested:
        cited = outcome.feature_total - len(outcome.feature_untested)
        parts.append(f"{cited} of {outcome.feature_total} scenarios of {outcome.feature} cited")
    if outcome.added_untested:
        parts.append(f"{len(outcome.added_untested)} new without a test")
    if outcome.lost:
        parts.append(f"{len(outcome.lost)} citations lost")
    if outcome.stale:
        parts.append(f"{len(outcome.stale)} citations of no scenario")
    return "; ".join(parts)


def details(outcome: Outcome) -> str:
    """The findings by name, for the scorecard's details."""
    sections = [
        ("Scenarios of the feature with no test", outcome.feature_untested),
        ("Scenarios this PR adds with no test", outcome.added_untested),
        ("Citations the base had and this PR dropped", outcome.lost),
        ("Citations of a scenario that does not exist (renamed or mistyped?)", outcome.stale),
    ]
    lines: list[str] = []
    for title, names in sections:
        if names:
            lines += [f"**{title}**", *[f"- {name}" for name in sorted(names)], ""]
    if outcome.failed:
        lines.append("A test cites its scenario in its docstring: `Scenario: <exact name>.` (or through pytest-bdd).")
    return "\n".join(lines)


def main() -> int:
    """Write the check's result for the scorecard."""
    args = _arguments()
    tests = tuple(glob.strip() for glob in args.tests.split(",") if glob.strip())
    head = Tree.scan(Path(args.root), tests)
    base = Tree.scan(Path(args.base_root), tests)
    feature = args.branch.split("/")[1] if args.branch.startswith("feature/") and "/" in args.branch else None
    outcome = judge(head, base, feature, args.final)
    result = {
        "check": "scenarios",
        "state": "fail" if outcome.failed else "pass",
        "headline": headline(outcome, head),
        "details": details(outcome),
    }
    Path(args.result).write_text(json.dumps(result))
    print(f"scenarios: {result['state']}: {result['headline']}")
    return 0


def _skipped(relative: str) -> bool:
    return any(part.startswith(".") or part in {"node_modules", "__pycache__"} for part in relative.split("/"))


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="the PR's checkout")
    parser.add_argument("--base-root", required=True, help="a checkout of the PR's merge base")
    parser.add_argument("--tests", required=True, help="globs of the test files, comma-separated")
    parser.add_argument("--branch", default="", help="the PR's head branch")
    parser.add_argument("--final", action="store_true", help="the PR goes into the default branch")
    parser.add_argument("--result", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
