"""The main plugin file containing all the fixtures."""

import pytest
from .terminal import Terminal


@pytest.fixture
def terminal():
    """The main fixture that enables terminal interaction."""
    return Terminal()
