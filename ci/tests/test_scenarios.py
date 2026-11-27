import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scenarios import Tree, citations_in, judge, scenarios_in  # noqa: E402

TESTS = ("tests/*",)
FEATURE = """Feature: Read a quantity

  Scenario: An amount is read
    Given a text

  # a comment between the tag and the scenario keeps the tag
  @documented-only
  Scenario: A manual check
    Given a person

  Scenario Outline: A unit is read
    Given <unit>

  Example: A zero is refused
    Given zero
"""


def tree(files: dict[str, str]) -> Tree:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for relative, text in files.items():
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(text)
        return Tree.scan(root, TESTS)


class TestParsing(unittest.TestCase):
    def test_every_scenario_keyword_and_the_tag(self) -> None:
        found = scenarios_in(FEATURE, "specs/q/q.feature")

        self.assertEqual([s.name for s in found], ["An amount is read", "A manual check", "A unit is read", "A zero is refused"])
        self.assertEqual([s.documented_only for s in found], [False, True, False, False])

    def test_a_tag_does_not_carry_past_another_line(self) -> None:
        found = scenarios_in("@documented-only\nFeature: F\n\n  Scenario: S\n", "f.feature")

        self.assertEqual([s.documented_only for s in found], [False])

    def test_docstring_citations_one_line_and_many(self) -> None:
        text = 'def test_a():\n    """Scenario: An amount is read."""\n\ndef test_b():\n    """\n    Scenario: A unit is read.\n    """\n'

        names, files = citations_in(text)

        self.assertEqual(names, {"An amount is read", "A unit is read"})
        self.assertEqual(files, [])

    def test_pytest_bdd_citations(self) -> None:
        text = '@scenario("q.feature", "A zero is refused")\ndef test_z():\n    pass\n\nscenarios("specs/q/other.feature")\n'

        names, files = citations_in(text)

        self.assertEqual(names, {"A zero is refused"})
        self.assertEqual(files, ["specs/q/other.feature"])


class TestTree(unittest.TestCase):
    def test_scenarios_binds_a_whole_file(self) -> None:
        scanned = tree({"specs/q/q.feature": FEATURE, "tests/test_q.py": 'scenarios("q/q.feature")\n'})

        self.assertEqual(scanned.uncited(), set())

    def test_only_test_files_cite(self) -> None:
        scanned = tree({"specs/q/q.feature": FEATURE, "src/q.py": '"""Scenario: An amount is read."""\n'})

        self.assertIn("An amount is read", scanned.uncited())


class TestJudge(unittest.TestCase):
    def base_and_head(self, head_tests: str, base_tests: str = "", final: bool = False):
        base = tree({"specs/q/q.feature": FEATURE, "tests/test_q.py": base_tests})
        head = tree({"specs/q/q.feature": FEATURE, "tests/test_q.py": head_tests})
        return judge(head, base, "q", final)

    def test_a_step_may_leave_scenarios_for_later_steps(self) -> None:
        outcome = self.base_and_head('"""Scenario: An amount is read."""')

        self.assertFalse(outcome.failed)

    def test_a_citation_of_no_scenario_fails(self) -> None:
        outcome = self.base_and_head('"""Scenario: An amount is red."""')

        self.assertEqual(outcome.stale, {"An amount is red"})
        self.assertTrue(outcome.failed)

    def test_a_dropped_citation_fails(self) -> None:
        outcome = self.base_and_head("", base_tests='"""Scenario: An amount is read."""')

        self.assertEqual(outcome.lost, {"An amount is read"})

    def test_a_scenario_added_without_a_test_fails(self) -> None:
        base = tree({"specs/q/q.feature": "Feature: F\n  Scenario: Old\n", "tests/test_q.py": '"""Scenario: Old."""'})
        head = tree({"specs/q/q.feature": "Feature: F\n  Scenario: Old\n  Scenario: New\n", "tests/test_q.py": '"""Scenario: Old."""'})

        self.assertEqual(judge(head, base, "q", final=False).added_untested, {"New"})

    def test_the_feature_pr_needs_every_scenario_of_its_feature(self) -> None:
        outcome = self.base_and_head('"""Scenario: An amount is read."""', final=True)

        self.assertEqual(outcome.feature_untested, {"A unit is read", "A zero is refused"})
        self.assertEqual(outcome.feature_total, 4)

    def test_the_feature_pr_ignores_other_features(self) -> None:
        files = {"specs/q/q.feature": "Feature: F\n  Scenario: Mine\n", "specs/other/o.feature": "Feature: O\n  Scenario: Theirs\n", "tests/test_q.py": '"""Scenario: Mine."""'}

        outcome = judge(tree(files), tree(files), "q", final=True)

        self.assertFalse(outcome.failed)


if __name__ == "__main__":
    unittest.main()
