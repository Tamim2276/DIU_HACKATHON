"""The dependency rule of the architecture, checked on every test run.

Imports may only point inward: presentation and infrastructure depend on
application and domain, application depends on domain, domain depends on nothing.
"""
import ast
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[2] / "app"

# layer -> layers it must not import from
FORBIDDEN = {
    "domain": {"application", "infrastructure", "presentation"},
    "application": {"infrastructure", "presentation"},
    "presentation": {"infrastructure"},
}
# The domain layer uses the standard library only.
THIRD_PARTY = {"fastapi", "joblib", "numpy", "pandas", "pydantic", "sklearn", "starlette"}


def imports_of(source: str, package: list[str]) -> set[str]:
    """Full names of the modules a file imports. `package` is the package the file lives in."""
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - (node.level - 1)] if node.level else []
            found.add(".".join(base + ([node.module] if node.module else [])))
    return found


def violations(layer: str) -> list[str]:
    bad = []
    for path in sorted((APP / layer).rglob("*.py")):
        package = list(path.relative_to(APP.parent).with_suffix("").parts[:-1])
        for module in sorted(imports_of(path.read_text(encoding="utf-8"), package)):
            parts = module.split(".")
            crosses_layer = parts[0] == "app" and len(parts) > 1 and parts[1] in FORBIDDEN[layer]
            if crosses_layer or (layer == "domain" and parts[0] in THIRD_PARTY):
                bad.append(f"{path.relative_to(APP).as_posix()} imports {module}")
    return bad


@pytest.mark.parametrize("layer", FORBIDDEN)
def test_layer_only_imports_inward(layer):
    assert violations(layer) == []


def test_the_check_sees_absolute_and_relative_imports():
    package = ["app", "domain", "entities"]
    assert imports_of("from app.infrastructure.config import settings", package) == {"app.infrastructure.config"}
    assert imports_of("from ...infrastructure import config", package) == {"app.infrastructure"}
    assert imports_of("from .user import User", package) == {"app.domain.entities.user"}
    assert imports_of("import pandas as pd", package) == {"pandas"}
