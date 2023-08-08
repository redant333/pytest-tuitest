import pytest
from .terminal import Terminal

@pytest.fixture
def terminal():
    return Terminal()
