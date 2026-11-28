import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_lens import failure  # noqa: E402

REFUSED_LOGIN = {"type": "result", "subtype": "success", "is_error": True, "result": "Failed to authenticate. API Error: 401 Invalid bearer token"}


class TestFailure(unittest.TestCase):
    def test_a_refused_login_is_a_failure_with_the_api_message(self) -> None:
        self.assertEqual(failure(1, REFUSED_LOGIN), "claude: Failed to authenticate. API Error: 401 Invalid bearer token")

    def test_no_json_names_the_exit_code(self) -> None:
        self.assertEqual(failure(2, None), "no JSON on stdout (exit 2)")

    def test_a_non_zero_exit_with_a_review_is_a_failure(self) -> None:
        self.assertEqual(failure(1, {"is_error": False, "structured_output": {"findings": []}}), "exit 1")

    def test_a_result_with_no_structured_output_is_a_failure(self) -> None:
        self.assertEqual(failure(0, {"is_error": False, "result": "done"}), "no structured output")

    def test_a_review_with_no_findings_is_not_a_failure(self) -> None:
        self.assertIsNone(failure(0, {"is_error": False, "structured_output": {"findings": []}}))


if __name__ == "__main__":
    unittest.main()
