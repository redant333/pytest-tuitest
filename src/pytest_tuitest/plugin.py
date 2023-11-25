"""The main plugin file containing all the fixtures."""

import pytest

from .terminal import Process, Terminal


class TuitestSetupException(Exception):
    """Raised when terminal fixture cannot be created."""


@pytest.fixture
def terminal(_tuitest_executable):
    """The main fixture that enables terminal interaction."""
    process = Process(_tuitest_executable)
    return Terminal(process)


@pytest.fixture
def _tuitest_executable(request):
    """Proxy fixture that enables setting the executable in terminal fixture."""
    if hasattr(request, "param") and request.param:
        return request.param

    msg = "Executable needs to be specified with test_executable decorator"
    raise TuitestSetupException(msg)


def test_executable(executable):
    """Decorator that enables setting the executable in terminal fixture."""
    return pytest.mark.parametrize("_tuitest_executable", [executable], indirect=True)
