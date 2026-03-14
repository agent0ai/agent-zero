from __future__ import annotations

import ast
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1] / "python" / "tools"


class ToolConstructorVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        inherits_tool = any(getattr(base, "id", None) == "Tool" for base in node.bases)
        if not inherits_tool:
            self.generic_visit(node)
            return

        init_fn = next(
            (n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == "__init__"),
            None,
        )

        if init_fn is None:
            # Inherit base Tool constructor directly. That's valid.
            return

        arg_names = [a.arg for a in init_fn.args.args]
        required = {"method", "args", "message", "loop_data"}
        if not required.issubset(set(arg_names)):
            self.violations.append(f"{node.name}.__init__ missing required args {sorted(required - set(arg_names))}")

        super_call_ok = False
        for n in ast.walk(init_fn):
            if not isinstance(n, ast.Call):
                continue
            if not (
                isinstance(n.func, ast.Attribute)
                and n.func.attr == "__init__"
                and isinstance(n.func.value, ast.Call)
                and isinstance(n.func.value.func, ast.Name)
                and n.func.value.func.id == "super"
            ):
                continue
            positional_args = [arg.id for arg in n.args if isinstance(arg, ast.Name)]
            if positional_args[:6] == ["agent", "name", "method", "args", "message", "loop_data"]:
                super_call_ok = True
                break

        if not super_call_ok:
            self.violations.append(
                f"{node.name}.__init__ must call super().__init__(agent, name, method, args, message, loop_data, ...)"
            )


def test_tool_constructor_signature_contract() -> None:
    violations: list[str] = []

    for path in sorted(TOOLS_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        visitor = ToolConstructorVisitor()
        visitor.visit(tree)
        for violation in visitor.violations:
            violations.append(f"{path.name}: {violation}")

    assert not violations, "\n".join(violations)
