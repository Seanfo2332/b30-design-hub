"""Load the single-file scripts as modules so tests can call their functions."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parent.parent


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"hub_{name}", ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def sync() -> ModuleType:
    return load_script("sync")


@pytest.fixture(scope="session")
def validate() -> ModuleType:
    return load_script("validate")
