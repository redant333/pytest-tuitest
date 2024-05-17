"""The main plugin file containing all the fixtures."""

import pytest

from .terminal import Process, Terminal

_EXECUTABLE_PARAM = "tuitest-default-executable"
_STDOUT_CAPTURE_PARAM = "tuitest-capture-stdout"
_STDERR_CAPTURE_PARAM = "tuitest-capture-stderr"


def addoption_executable(parser):
    """Add ini and command line options for specifying default executable."""
    help_text = "Executable to be used for tests when the executable isn't explicitly specified."

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


def addoption_stdout_capture(parser):
    """Add ini option for specifying whether stdout should be captured by default."""
    parser.addini(
        name=_STDOUT_CAPTURE_PARAM,
        type="bool",
        help="Whether to capture stdout when capturing stdout is not explicitly" +
             " specified. False by default."
    )


def addoption_stderr_capture(parser):
    """Add ini option for specifying whether stderr should be captured by default."""
    parser.addini(
        name=_STDERR_CAPTURE_PARAM,
        type="bool",
        help="Whether to capture stderr when capturing stderr is not explicitly" +
             " specified. False by default."
    )


def pytest_addoption(parser):
    """Add tuitest-specific options."""
    addoption_executable(parser)
    addoption_stdout_capture(parser)
    addoption_stderr_capture(parser)


class TuitestSetupException(Exception):
    """Raised when terminal fixture cannot be created."""

###############################################################################
# Fixtures
###############################################################################


@pytest.fixture
def terminal(tuitest_executable, tuitest_arguments, tuitest_capture_stdout, tuitest_capture_stderr):
    """The main fixture that enables terminal interaction."""
    process = Process(executable=tuitest_executable,
                      args=tuitest_arguments,
                      capture_stdout=tuitest_capture_stdout,
                      capture_stderr=tuitest_capture_stderr)
    return Terminal(process)


@pytest.fixture(name="tuitest_executable")
def fixture_tuitest_executable(request):
    """Fixture that defines the executable used in terminal fixture.

    The return value of this fixture is, in the order of priority, are:
    - The value specified with test_executable decorator or @pytest.mark.parametrize
      with indirect flag
    - The value specified with command line option --tuitest-default-executable
    - The value specified by using pytest.ini option tuitest-default-executable

    If the default executable is not specified in any of the listed ways, an exception
    is raised.
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

    The return value of this fixture is, in the order of priority, are:
    - The value specified with with_captured_stdout decorator or @pytest.mark.parametrize
      with indirect flag
    - The value specified by using pytest.ini option tuitest-capture-stdout
    - False
    """
    if hasattr(request, "param"):
        return request.param

    if ini_capture_stdout := request.config.getini(_STDOUT_CAPTURE_PARAM):
        return ini_capture_stdout

    return False


@pytest.fixture(name="tuitest_capture_stderr")
def fixture_capture_stderr(request):
    """Fixture that defines whether the stderr of the executable is captured.

    If it's not captured, it will be displayed in the virtual terminal.

    The return value of this fixture is, in the order of priority, are:
    - The value specified with with_captured_stderr decorator or @pytest.mark.parametrize
      with indirect flag
    - The value specified by using pytest.ini option tuitest-capture-stderr
    - False
    """
    if hasattr(request, "param"):
        return request.param

    if ini_capture_stderr := request.config.getini(_STDERR_CAPTURE_PARAM):
        return ini_capture_stderr

    return False
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


def with_captured_stderr(capture_stderr: bool = True):
    """Capture stderr instead of showing it in the virtual terminal.

    The captured stderr is availabale in the output of Terminal::wait_for_finished.
    Note: This is a decorator intended to be applied to a test function.

    Args:
        capture_stderr (bool, optional): Whether the stderr output should be captured. Defaults
            to True.
    """
    return pytest.mark.parametrize("tuitest_capture_stderr", [capture_stderr], indirect=True)
