import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interface import changes_between, declared_documents, interface_of, verdict  # noqa: E402

SOURCE, TESTS = ("src/*",), ("tests/*", "*/tests/*")
MODELS = '''
from enum import StrEnum
from dataclasses import dataclass

MAX = 10
_LIMIT = 3


class Unit(StrEnum):
    GRAM = "g"


@dataclass(frozen=True)
class Quantity:
    amount: float
    unit: Unit

    def __post_init__(self) -> None:
        pass

    def scaled(self, factor: float) -> "Quantity":
        return self

    def _check(self) -> None:
        pass


def read(text: str) -> Quantity:
    return Quantity(1, Unit.GRAM)


def _helper() -> None:
    pass
'''


def interface(files: dict[str, str]) -> dict[tuple[str, str], str]:
    with tempfile.TemporaryDirectory() as folder:
        root = Path(folder)
        for relative, text in files.items():
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(text)
        return interface_of(root, SOURCE, TESTS)


class TestInterface(unittest.TestCase):
    def test_public_items_of_public_modules_only(self) -> None:
        items = interface({"src/q/models.py": MODELS, "src/q/_rules.py": "def rule() -> None: ...\n", "src/q/_impl/x.py": "def x() -> None: ...\n", "src/q/tests/test_m.py": "def test_m() -> None: ...\n"})

        self.assertEqual(sorted(name for _, name in items), ["MAX", "Quantity", "Unit", "read"])

    def test_a_class_shape_holds_fields_members_and_public_methods(self) -> None:
        shape = interface({"src/q/models.py": MODELS})[("src/q/models.py", "Quantity")]

        self.assertIn("amount: float", shape)
        self.assertIn("def scaled(self, factor: float) -> 'Quantity'", shape)
        self.assertNotIn("_check", shape)
        self.assertNotIn("__post_init__", shape)

    def test_a_body_change_is_no_interface_change(self) -> None:
        before = interface({"src/q/models.py": MODELS})
        after = interface({"src/q/models.py": MODELS.replace("return Quantity(1, Unit.GRAM)", "return Quantity(2, Unit.GRAM)")})

        self.assertEqual(changes_between(before, after), [])

    def test_added_removed_and_changed(self) -> None:
        before = interface({"src/q/models.py": MODELS})
        changed = MODELS.replace('GRAM = "g"', 'GRAM = "g"\n    LITRE = "l"').replace("def read(text: str)", "def read(text: str, strict: bool)").replace("MAX = 10\n", "")
        after = interface({"src/q/models.py": changed, "src/q/errors.py": "class QuantityError(ValueError): ...\n"})

        kinds = {change.name: change.kind for change in changes_between(before, after)}

        self.assertEqual(kinds, {"MAX": "removed", "Unit": "changed", "read": "changed", "QuantityError": "added"})


class TestDeclaration(unittest.TestCase):
    def test_each_change_must_be_named_in_the_declared_folder(self) -> None:
        changes = changes_between({}, interface({"src/q/models.py": MODELS}))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "specs/q").mkdir(parents=True)
            (root / "specs/q/plan.md").write_text("Adds `Unit`, `Quantity` and `read(text)`.")

            declared, documents = declared_documents("Intro\nInterface change: `specs/q/`\n", root)
            state, line = verdict(changes, declared, documents)

        self.assertEqual(declared, "specs/q")
        self.assertEqual(state, "fail")
        self.assertIn("1 not named", line)

    def test_named_everywhere_passes(self) -> None:
        changes = changes_between({}, interface({"src/q/models.py": MODELS}))

        self.assertEqual(verdict(changes, "specs/q", "MAX Unit Quantity read")[0], "pass")

    def test_a_name_inside_a_longer_word_is_not_named(self) -> None:
        changes = changes_between({}, interface({"src/q/models.py": "def read() -> None: ...\n"}))

        self.assertEqual(verdict(changes, "specs/q", "It is already done.")[0], "fail")

    def test_no_declaration_fails(self) -> None:
        changes = changes_between({}, interface({"src/q/models.py": MODELS}))

        self.assertEqual(verdict(changes, None, "")[0], "fail")

    def test_a_declared_path_outside_the_repo_reads_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            declared, documents = declared_documents("Interface change: ../../etc\n", Path(folder))

        self.assertEqual((declared, documents), ("../../etc", ""))

    def test_no_change_passes_without_a_declaration(self) -> None:
        self.assertEqual(verdict([], None, "")[0], "pass")


if __name__ == "__main__":
    unittest.main()
