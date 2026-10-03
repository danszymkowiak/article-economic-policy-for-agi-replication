import ast
import pathlib

import llm_panel.domain as domain_pkg

FORBIDDEN_IMPORTS = {
    "os", "pathlib", "sys", "socket", "subprocess", "shutil", "tempfile", "sqlite3",
    "requests", "httpx", "urllib", "yaml", "io", "time", "datetime", "logging",
}  # fmt: skip
# `random` is allowed: the domain only uses explicitly seeded random.Random instances.
FORBIDDEN_CALLS = {"open", "print", "input"}


def domain_files():
    return sorted(pathlib.Path(domain_pkg.__file__).parent.glob("*.py"))


def test_domain_modules_do_no_io():
    assert domain_files()
    for path in domain_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                roots = {(node.module or "").split(".")[0]} if node.level == 0 else set()
            else:
                roots = set()
            assert not roots & FORBIDDEN_IMPORTS, f"{path.name} imports {roots & FORBIDDEN_IMPORTS}"
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in FORBIDDEN_CALLS, f"{path.name} calls {node.func.id}"


def test_domain_holds_no_vendor_specific_code():
    # vendor wire formats live with their adapter, not in the domain layer
    for path in domain_files():
        assert "zen" not in path.name, path.name
        assert "opencode" not in path.read_text().lower(), f"{path.name} mentions a vendor"
