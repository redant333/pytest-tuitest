"""Utilities for testing the library."""
from pathlib import Path

import pytest

pytest_plugins = ["pytester"]


@pytest.fixture
def test_scripts_dir(request) -> Path:
    """Get the location of the folder with scripts for testing."""
    return Path(request.config.rootdir) / "tests" / "test_scripts"
