"""Check that a PR changes the public interface only where its spec names the change.

The public interface is the top-level names of the public modules: source files with no part of
their path starting with "_" (except `__init__.py`), and no test files. A class is one item: its
decorators, bases, fields, members and public method signatures. A function is its signature; a
constant is its assignment. Bodies are not part of the interface.

Any added, removed or changed item fails the check, unless the PR description has a line
`Interface change: <spec folder or file>` and every changed item's name appears in a Markdown
file there (the spec, the plan or the brief the user approved).
"""

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

DECLARATION = re.compile(r"^[ \t]*interface change:[ \t]*(\S.*?)[ \t]*$", re.IGNORECASE | re.MULTILINE)
KEPT_DUNDERS = {"__init__", "__call__"}


@dataclass(frozen=True)
class Change:
    """One public item that differs between the base and the PR."""

    module: str
    name: str
    before: str | None
    after: str | None

    @property
    def kind(self) -> str:
        """Added, removed or changed."""
        return "added" if self.before is None else "removed" if self.after is None else "changed"


def interface_of(root: Path, source: tuple[str, ...], tests: tuple[str, ...]) -> dict[tuple[str, str], str]:
    """Every public item under root, keyed by module path and name, with its shape as text."""
    items: dict[tuple[str, str], str] = {}
    for path in sorted(root.rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        if _public_module(relative, source, tests):
            tree = ast.parse(path.read_text(), filename=relative)
            items |= {(relative, name): shape for name, shape in _items(tree)}
    return items


def changes_between(base: dict[tuple[str, str], str], head: dict[tuple[str, str], str]) -> list[Change]:
    """The items added, removed or changed from base to head."""
    keys = sorted(set(base) | set(head))
    return [Change(key[0], key[1], base.get(key), head.get(key)) for key in keys if base.get(key) != head.get(key)]


def unnamed(changes: list[Change], documents: str) -> list[Change]:
    """The changes whose name the declared documents never mention."""
    return [change for change in changes if not re.search(rf"\b{re.escape(change.name)}\b", documents)]


def declared_documents(body: str, root: Path) -> tuple[str | None, str]:
    """The declared spec path from the PR description, and the text of its Markdown files."""
    match = DECLARATION.search(body)
    if not match:
        return None, ""
    declared = match.group(1).strip("`").rstrip("/")
    target = (root / declared).resolve()
    if ".." in Path(declared).parts or not target.is_relative_to(root.resolve()) or not target.exists():
        return declared, ""
    files = [target] if target.is_file() else sorted(target.rglob("*.md"))
    return declared, "\n".join(path.read_text() for path in files)


def verdict(changes: list[Change], declared: str | None, documents: str) -> tuple[str, str]:
    """The state and the headline."""
    if not changes:
        return "pass", "no change to the public interface"
    count = f"{len(changes)} public item{'s' if len(changes) != 1 else ''} changed"
    if declared is None:
        return "fail", f"{count}, and the PR declares no interface change"
    if not documents:
        return "fail", f"{count}; the declared `{declared}` holds no Markdown file"
    missing = unnamed(changes, documents)
    if missing:
        return "fail", f"{count}; {len(missing)} not named in `{declared}`"
    return "pass", f"{count}, each named in `{declared}`"


def details(changes: list[Change], declared: str | None, documents: str) -> str:
    """Each change with its before and after, and what to do."""
    missing = {(c.module, c.name) for c in unnamed(changes, documents)} if declared else set()
    lines: list[str] = []
    for change in changes:
        flag = " (not named in the spec)" if (change.module, change.name) in missing else ""
        lines.append(f"- **{change.kind}** `{change.module}`: `{change.name}`{flag}")
        if change.before and change.after:
            lines += ["  ```diff", *[f"  - {line}" for line in change.before.splitlines()], *[f"  + {line}" for line in change.after.splitlines()], "  ```"]
    if changes and (declared is None or missing or not documents):
        lines += [
            "",
            "A public interface changes only when the spec names the change. If the approved spec or "
            "plan names it, add a line `Interface change: specs/<feature>/` to the PR description; "
            "if not, undo the change or ask the user.",
        ]
    return "\n".join(lines)


def _items(tree: ast.Module) -> list[tuple[str, str]]:
    found: list[tuple[str, str]] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _public(node.name):
            found.append((node.name, _signature(node)))
        elif isinstance(node, ast.ClassDef) and _public(node.name):
            found.append((node.name, _class_shape(node)))
        elif isinstance(node, ast.Assign):
            found += [(target.id, ast.unparse(node)) for target in node.targets if isinstance(target, ast.Name) and _public(target.id) and target.id != "__all__"]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and _public(node.target.id):
            found.append((node.target.id, ast.unparse(node)))
        elif isinstance(node, ast.TypeAlias) and _public(node.name.id):
            found.append((node.name.id, ast.unparse(node)))
    return found


def _signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list]
    prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
    returns = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    return "\n".join([*decorators, f"{prefix} {node.name}({ast.unparse(node.args)}){returns}"])


def _class_shape(node: ast.ClassDef) -> str:
    decorators = [f"@{ast.unparse(d)}" for d in node.decorator_list]
    bases = ", ".join(ast.unparse(b) for b in [*node.bases, *node.keywords])
    body: list[str] = []
    for member in node.body:
        if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)) and (_public(member.name) or member.name in KEPT_DUNDERS):
            body.append(_signature(member))
        elif isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name) and _public(member.target.id):
            body.append(ast.unparse(member))
        elif isinstance(member, ast.Assign) and any(isinstance(t, ast.Name) and _public(t.id) for t in member.targets):
            body.append(ast.unparse(member))
    return "\n".join([*decorators, f"class {node.name}({bases}):", *[f"    {line}" for item in body for line in item.splitlines()]])


def _public(name: str) -> bool:
    return not name.startswith("_")


def _public_module(relative: str, source: tuple[str, ...], tests: tuple[str, ...]) -> bool:
    if not any(fnmatch(relative, glob) for glob in source) or any(fnmatch(relative, glob) for glob in tests):
        return False
    parts = relative.split("/")
    return all(not part.startswith("_") for part in parts[:-1]) and (parts[-1] == "__init__.py" or not parts[-1].startswith("_"))


def _globs(text: str) -> tuple[str, ...]:
    return tuple(glob.strip() for glob in text.split(",") if glob.strip())


def main() -> int:
    """Write the check's result for the scorecard."""
    args = _arguments()
    source, tests = _globs(args.source), _globs(args.tests)
    root = Path(args.root)
    changes = changes_between(interface_of(Path(args.base_root), source, tests), interface_of(root, source, tests))
    declared, documents = declared_documents(Path(args.body).read_text(), root)
    state, line = verdict(changes, declared, documents)
    result = {"check": "interface", "state": state, "headline": line, "details": details(changes, declared, documents)}
    Path(args.result).write_text(json.dumps(result))
    print(f"interface: {state}: {line}")
    return 0


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="the PR's checkout")
    parser.add_argument("--base-root", required=True, help="a checkout of the PR's merge base")
    parser.add_argument("--source", required=True)
    parser.add_argument("--tests", required=True)
    parser.add_argument("--body", required=True, help="a file holding the PR's description")
    parser.add_argument("--result", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())
