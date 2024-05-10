"""The main plugin file containing all the fixtures."""

import pytest

from .terminal import Process, Terminal

_EXECUTABLE_PARAM = "tuitest-default-executable"


def addoption_executable(parser):
    """Add ini and command line options for specifying default executable."""
    help_text = "Executable to be used for tests when the executable it isn't explicitly specified."

    parser.addini(
        name=_EXECUTABLE_PARAM,
        type="string",
        help=help_text,
    )

    parser.addoption(
        f"--{_EXECUTABLE_PARAM}",
        dest=_EXECUTABLE_PARAM,
        help=help_text,
    )


def pytest_addoption(parser):
    """Add tuitest-specific options."""
    addoption_executable(parser)


class TuitestSetupException(Exception):
    """Raised when terminal fixture cannot be created."""

###############################################################################
# Fixtures
###############################################################################


@pytest.fixture
def terminal(tuitest_executable, tuitest_arguments, tuitest_capture_stdout):
    """The main fixture that enables terminal interaction."""
    process = Process(executable=tuitest_executable,
                      args=tuitest_arguments, capture_stdout=tuitest_capture_stdout)
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

    if cli_executable := request.config.getoption(_EXECUTABLE_PARAM, default=None):
        return cli_executable

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


@pytest.fixture(name="tuitest_capture_stdout")
def fixture_capture_stdout(request):
    """Fixture that defines whether the stdout of the executable is captured.

    If it's not captured, it will be displayed in the virtual terminal.

    This fixture can be parametrized by using with_captured_stdout decorator or
    @pytest.mark.parametrize with indirect flag. If it's not parametrized, it
    returns False.
    """
    return getattr(request, "param", False)

###############################################################################
# Decorators
###############################################################################


def test_executable(executable):
    """Use this executable for the test.

    Note: This is a decorator intended to be applied to a test function.
    """
    return pytest.mark.parametrize("tuitest_executable", [executable], indirect=True)


def with_arguments(args):
    """Send these arguments to the executable.

    Note: This is a decorator intended to be applied to a test function."""
    return pytest.mark.parametrize("tuitest_arguments", [args], indirect=True)


def with_captured_stdout(capture_output: bool = True):
    """Capture stdout instead of showing it in the virtual terminal.

    The captured stdout is availabale in the output of Terminal::wait_for_finished.
    Note: This is a decorator intended to be applied to a test function.

    Args:
        capture_output (bool, optional): Whether the output should be captured. Defaults
            to True.
    """
    return pytest.mark.parametrize("tuitest_capture_stdout", [capture_output], indirect=True)
