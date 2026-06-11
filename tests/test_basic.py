"""Basic tests for the Hinglish dictionary project structure."""

import importlib
import pathlib


def test_project_structure():
    """Verify key directories and files exist."""
    root = pathlib.Path(__file__).parent.parent
    assert (root / "src").is_dir()
    assert (root / "data").is_dir()
    assert (root / "tests").is_dir()
    assert (root / "pyproject.toml").is_file()
    assert (root / "README.md").is_file()


def test_package_importable():
    """Verify the main package is importable."""
    mod = importlib.import_module("src")
    assert hasattr(mod, "__version__")
    assert mod.__version__ == "1.0.0"
