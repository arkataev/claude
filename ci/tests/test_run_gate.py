import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from run_gate import failed_targets, result, run  # noqa: E402

MAKE_K_OUTPUT = """uv run ruff check src tests
src/a.py:1:1: F401 unused import
make: *** [Makefile:6: lint] Error 1
uv run mypy
make[1]: *** [typecheck] Error 1
make: *** [Makefile:6: lint] Error 1
make: Target 'test' not remade because of errors.
"""


class TestGate(unittest.TestCase):
    def test_failed_make_targets_once_each_in_order(self) -> None:
        self.assertEqual(failed_targets(MAKE_K_OUTPUT), ["lint", "typecheck"])

    def test_a_pass_has_no_details(self) -> None:
        gate = result("make -k test", 0, "all good\n", 12.4)

        self.assertEqual((gate["state"], gate["headline"], gate["details"]), ("pass", "`make -k test` passed in 12 s", ""))

    def test_a_failure_names_the_targets_and_keeps_the_tail(self) -> None:
        output = "".join(f"line {n}\n" for n in range(100)) + MAKE_K_OUTPUT

        gate = result("make -k test", 2, output, 20)

        self.assertEqual(gate["state"], "fail")
        self.assertIn("(exit 2) in 20 s: lint, typecheck", gate["headline"])
        self.assertIn("not remade because of errors", gate["details"])
        self.assertNotIn("line 40\n", gate["details"])

    def test_run_returns_the_exit_code_and_the_merged_output(self) -> None:
        code, output = run("echo out; echo err >&2; exit 3")

        self.assertEqual(code, 3)
        self.assertEqual(sorted(output.split()), ["err", "out"])


if __name__ == "__main__":
    unittest.main()
