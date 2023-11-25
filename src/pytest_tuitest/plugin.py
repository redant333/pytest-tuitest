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

###############################################################################
# Fixtures
###############################################################################


@pytest.fixture
def terminal(tuitest_executable, tuitest_arguments):
    """The main fixture that enables terminal interaction."""
    process = Process(executable=tuitest_executable, args=tuitest_arguments)
    return Terminal(process)


@pytest.fixture(name="tuitest_executable")
def fixture_tuitest_executable(request):
    """Fixture that defines the executable used in terminal fixture.

    It can be parametrized by using test_executable decorator or @pytest.mark.parametrize
    with indirect flag. If it's not parametrized, it will return the value of ini parameter
    tuitest_default_executable. If tuitest_default_executable is not defined, it raises an
    exception.
    """
    if hasattr(request, "param") and request.param:
        return request.param

    if ini_executable := request.config.getini(_EXECUTABLE_PARAM):
        return ini_executable

    msg = ("Executable needs to be specified with test_executable decorator or "
           f"{_EXECUTABLE_PARAM} ini option.")
    raise TuitestSetupException(msg)


@pytest.fixture(name="tuitest_arguments")
def fixture_tuitest_arguments(request):
    """Fixture that defines the arguments sent to the executable used in terminal fixture.

    It can be parametrized by using with_arguments decorator or @pytest.mark.parametrize
    with indirect flag. If it's not parametrized, an empty argument list is used.
    """
    if hasattr(request, "param"):
        return request.param

    return None

###############################################################################
# Decorators
###############################################################################


def test_executable(executable):
    """Decorator that enables setting the executable used in terminal fixture."""
    return pytest.mark.parametrize("tuitest_executable", [executable], indirect=True)


def with_arguments(args):
    """Decorator that enables setting the executable arguments used in terminal fixture."""
    return pytest.mark.parametrize("tuitest_arguments", [args], indirect=True)
