import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "merge_findings.py"
REVIEW = {"gate": {"passed": True, "summary": "make -k test passed"}, "findings": [], "clean_areas": [], "report": "clean"}


def lens(name: str, error: str | None, structured: dict[str, object] | None) -> dict[str, object]:
    claude = {"is_error": error is not None, "structured_output": structured, "total_cost_usd": 0.1, "num_turns": 3}
    return {"lens": name, "agent": "solid-reviewer-ci", "preloaded": {}, "exit_code": 0 if error is None else 1, "error": error, "duration_s": 1.0, "claude": claude}


class TestSilentLenses(unittest.TestCase):
    def merge(self, *lenses: dict[str, object]) -> tuple[str, str]:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "lenses").mkdir()
            for item in lenses:
                (root / "lenses" / f"{item['lens']}.json").write_text(json.dumps(item))
            (root / "pr.diff").write_text("")
            subprocess.run(
                [sys.executable, str(SCRIPT), "--lenses", str(root / "lenses"), "--diff", str(root / "pr.diff"), "--pr", "1", "--commit", "abc",
                 "--out", str(root / "findings.json"), "--review", str(root / "review.json"), "--state", str(root / "state.txt")],
                check=True, capture_output=True,
            )
            body = json.loads((root / "review.json").read_text())["body"]
            return (root / "state.txt").read_text(), body

    def test_a_refused_login_fails_and_never_reads_as_no_findings(self) -> None:
        state, body = self.merge(lens("whole", "claude: Failed to authenticate. API Error: 401 Invalid bearer token", None))

        self.assertEqual(state, "failed")
        self.assertIn("FAILED: no lens", body)
        self.assertIn("401 Invalid bearer token", body)
        self.assertNotIn("0 findings", body)

    def test_one_silent_lens_of_two_fails_and_is_named(self) -> None:
        state, body = self.merge(lens("tests", None, REVIEW), lens("design", "no structured output", None))

        self.assertEqual(state, "failed")
        self.assertIn("0 findings from 1 lenses", body)
        self.assertIn("1 failed", body)
        self.assertIn("design: no structured output", body)

    def test_every_lens_answering_is_ok(self) -> None:
        state, body = self.merge(lens("whole", None, REVIEW))

        self.assertEqual(state, "ok")
        self.assertNotIn("Not a full review", body)


if __name__ == "__main__":
    unittest.main()
