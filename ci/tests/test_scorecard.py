import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scorecard import comment, overall, summary  # noqa: E402


def row(check: str, state: str, details: str = "") -> dict[str, str]:
    return {"check": check, "state": state, "headline": f"{check} headline", "details": details}


class TestScorecard(unittest.TestCase):
    def test_the_worst_state_wins(self) -> None:
        self.assertEqual(overall([row("size", "warn"), row("gate", "pass")]), "warn")
        self.assertEqual(overall([row("size", "exempt"), row("gate", "fail")]), "fail")
        self.assertEqual(overall([row("size", "exempt"), row("gate", "pass")]), "exempt")
        self.assertEqual(overall([row("gate", "pass")]), "pass")

    def test_the_summary_has_every_row_and_the_details_of_what_did_not_pass(self) -> None:
        text = summary([row("gate", "pass", "gate output"), row("scenarios", "fail", "- A zero amount is refused")])

        self.assertIn("- gate: pass: gate headline", text)
        self.assertIn("- scenarios: fail: scenarios headline", text)
        self.assertIn("- A zero amount is refused", text)
        self.assertNotIn("gate output", text)

    def test_the_comment_opens_the_details_of_a_failure_only(self) -> None:
        text = comment([row("size", "pass", "counts"), row("interface", "fail", "changes")])

        self.assertIn("<details><summary>size</summary>", text)
        self.assertIn("<details open><summary>interface</summary>", text)


if __name__ == "__main__":
    unittest.main()
