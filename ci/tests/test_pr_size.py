import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pr_size import Kind, Patterns, State, judge, tally  # noqa: E402

PATTERNS = Patterns(source=("src/*",), tests=("tests/*", "*/tests/*", "*test_*.py"), ignored=("uv.lock", "*/generated/*"))


def changed(path: str, added: int, deleted: int = 0) -> dict[str, object]:
    return {"filename": path, "additions": added, "deletions": deleted}


class TestKinds(unittest.TestCase):
    def test_each_kind(self) -> None:
        cases = {
            "src/quantity/models.py": Kind.SOURCE,
            "tests/test_reading.py": Kind.TESTS,
            "src/pantry/product/tests/test_x.py": Kind.TESTS,
            "uv.lock": Kind.IGNORED,
            "src/app/generated/schema.py": Kind.IGNORED,
            "specs/a/spec.md": Kind.OTHER,
            "README.md": Kind.OTHER,
        }

        kinds = {path: PATTERNS.kind_of(path) for path in cases}

        self.assertEqual(kinds, cases)


class TestTally(unittest.TestCase):
    def test_added_and_deleted_lines_sum_per_kind(self) -> None:
        files = [changed("src/a.py", 10, 5), changed("src/b.py", 3), changed("tests/test_a.py", 40), changed("uv.lock", 900)]

        tallies = tally(files, PATTERNS)

        self.assertEqual((tallies[Kind.SOURCE].lines, tallies[Kind.SOURCE].files), (18, 2))
        self.assertEqual(tallies[Kind.TESTS].lines, 40)
        self.assertEqual(tallies[Kind.IGNORED].lines, 900)
        self.assertEqual(tallies[Kind.OTHER].lines, 0)


class TestJudge(unittest.TestCase):
    def test_at_the_warning_passes(self) -> None:
        self.assertEqual(judge(400, 400, 800, [], "").state, State.PASS)

    def test_over_the_warning_warns(self) -> None:
        self.assertEqual(judge(401, 400, 800, [], "").state, State.WARN)

    def test_at_the_cap_warns(self) -> None:
        self.assertEqual(judge(800, 400, 800, [], "").state, State.WARN)

    def test_over_the_cap_fails_and_says_not_to_compress(self) -> None:
        verdict = judge(801, 400, 800, [], "")

        self.assertEqual(verdict.state, State.FAIL)
        self.assertIn("Do not compress", verdict.message)

    def test_exempt_with_a_reason_passes(self) -> None:
        verdict = judge(5000, 400, 800, ["size-exempt"], "Intro.\nSize exempt: removes the old chat\n")

        self.assertEqual(verdict.state, State.EXEMPT)
        self.assertIn("removes the old chat", verdict.message)

    def test_exempt_without_a_reason_fails(self) -> None:
        verdict = judge(5000, 400, 800, ["size-exempt"], "Size exempt:   \n")

        self.assertEqual(verdict.state, State.FAIL)
        self.assertIn("no reason", verdict.message)

    def test_an_empty_reason_does_not_take_the_next_line(self) -> None:
        verdict = judge(5000, 400, 800, ["size-exempt"], "Size exempt:\nThe step adds the list.\n")

        self.assertEqual(verdict.state, State.FAIL)

    def test_a_reason_without_the_label_does_not_exempt(self) -> None:
        self.assertEqual(judge(900, 400, 800, [], "Size exempt: big").state, State.FAIL)


if __name__ == "__main__":
    unittest.main()
