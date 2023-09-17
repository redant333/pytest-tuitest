"""The main plugin file containing all the fixtures."""

import pytest

from .terminal import Process, Terminal


@pytest.fixture
def terminal():
    """The main fixture that enables terminal interaction."""
    # Use a dummy executable for now
    process = Process("sh", ["-c", "echo Works"])
    return Terminal(process)
