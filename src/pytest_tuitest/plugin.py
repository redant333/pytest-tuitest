"""The main plugin file containing all the fixtures."""

import pytest

from .terminal import Process, Terminal

_EXECUTABLE_PARAM = "tuitest_default_executable"


def pytest_addoption(parser):
    """Add tuitest-specific options."""
    parser.addini(
        name=_EXECUTABLE_PARAM,
        type="string",
        help="Executable to be used for tests when the executable it isn't explicitly specified."
    )


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

    if ini_executable := request.config.getini(_EXECUTABLE_PARAM):
        return ini_executable

    msg = ("Executable needs to be specified with test_executable decorator or "
           f"{_EXECUTABLE_PARAM} ini option.")
    raise TuitestSetupException(msg)


def test_executable(executable):
    """Decorator that enables setting the executable in terminal fixture."""
    return pytest.mark.parametrize("_tuitest_executable", [executable], indirect=True)
