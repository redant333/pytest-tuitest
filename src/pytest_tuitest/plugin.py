"""This module contains all the pytest fixtures, decorators and options.

The main fixture, that is requested in tests, is `terminal`.
It depends on the other fixtures in this module and customizing them allows you
to customize the terminal environment in which your process will run.

# Fixtures vs Decorators

Each of the fixtures can be customized either by using the corresponding decorators
or by using `pytest.mark.parametrize` with the indirect flag:

```python
        @tt.with_terminal_size(21, 22)
        def test_foo(terminal):
```

```python
        @pytest.mark.parametrize("tuitest_terminal_size", indirect=True, argvalues=[
            (21, 22),
            (23, 24),
        ])
        def test_foo(terminal):
```

Decorators are more convenient when there is only one input, while `pytest.mark.parametrize`
is more convenient when you want to parametrize the test, i.e. run the same test with multiple
different inputs.

# Specifying fixture values globally

Values for some of the fixtures can be specified once in `pytest.ini` or in a command-line argument
and you don't need to specify them in your tests.

For example, your whole project will likely test the same executable and, in order to avoid putting
`test_executable` everywhere, you can just put
`tuitest-default-executable = /path/to/your/executable` in `pytest.ini`.
Explicit `test_executable` will still override this value when that is needed.

The fixtures that allow setting the value through `pytest.ini` option or command-line argument
have a note in their documentation with the details.
"""

import pytest

from .terminal import Process, Terminal

_EXECUTABLE_PARAM = "tuitest-default-executable"
_STDOUT_CAPTURE_PARAM = "tuitest-capture-stdout"
_STDERR_CAPTURE_PARAM = "tuitest-capture-stderr"


def addoption_executable(parser):
    """@private Add ini and command line options for specifying default executable."""
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
    """@private Add ini option for specifying whether stdout should be captured by default."""
    parser.addini(
        name=_STDOUT_CAPTURE_PARAM,
        type="bool",
        help="Whether to capture stdout when capturing stdout is not explicitly" +
             " specified. False by default."
    )


def addoption_stderr_capture(parser):
    """@private Add ini option for specifying whether stderr should be captured by default."""
    parser.addini(
        name=_STDERR_CAPTURE_PARAM,
        type="bool",
        help="Whether to capture stderr when capturing stderr is not explicitly" +
             " specified. False by default."
    )


def pytest_addoption(parser):
    """@private Add tuitest-specific options."""
    addoption_executable(parser)
    addoption_stdout_capture(parser)
    addoption_stderr_capture(parser)


class TuitestSetupException(Exception):
    """@private Raised when terminal fixture cannot be created."""

###############################################################################
# Fixtures
###############################################################################


@pytest.fixture
# The terminal can be parametrized in many ways and each of those is a fixture.
# No point in grouping them the arguments in any way.
# pylint: disable-next=too-many-arguments
def terminal(tuitest_executable,
             tuitest_arguments,
             tuitest_env,
             tuitest_capture_stdout,
             tuitest_capture_stderr,
             tuitest_stdin,
             tuitest_terminal_size) -> Terminal:
    """The main fixture that enables terminal interaction."""
    columns, lines = tuitest_terminal_size

    process = Process(executable=tuitest_executable,
                      args=tuitest_arguments,
                      additional_env=tuitest_env,
                      capture_stdout=tuitest_capture_stdout,
                      capture_stderr=tuitest_capture_stderr,
                      stdin=tuitest_stdin,
                      lines=lines,
                      columns=columns)
    return Terminal(process)


@pytest.fixture(name="tuitest_executable")
def fixture_tuitest_executable(request):
    """Fixture that defines the executable used in terminal fixture.

    The return value of this fixture is, in the order of priority, are:
    - The value specified with `test_executable` decorator or `@pytest.mark.parametrize`
      with indirect flag
    - The value specified with command line option `--tuitest-default-executable`
    - The value specified by using pytest.ini option `tuitest-default-executable`

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

    It can be parametrized by using `with_arguments` decorator or `@pytest.mark.parametrize`
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
    - The value specified with `with_captured_stdout` decorator or `@pytest.mark.parametrize`
      with indirect flag
    - The value specified by using pytest.ini option `tuitest-capture-stdout`
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
    - The value specified with `with_captured_stderr` decorator or `@pytest.mark.parametrize`
      with indirect flag
    - The value specified by using pytest.ini option `tuitest-capture-stderr`
    - False
    """
    if hasattr(request, "param"):
        return request.param

    if ini_capture_stderr := request.config.getini(_STDERR_CAPTURE_PARAM):
        return ini_capture_stderr

    return False


@pytest.fixture(name="tuitest_stdin")
def fixture_stdin(request):
    """Fixture that determines the stdin to be sent to the executable.

    It can be parametrized by using `with_stdin` decorator or `@pytest.mark.parametrize`
    with indirect flag. If it's not parametrized, no stdin will be sent to the executable.
    """
    if hasattr(request, "param"):
        return request.param.encode("utf8")

    return None


@pytest.fixture(name="tuitest_terminal_size")
def fixture_terminal_size(request):
    """Fixture that determines the size of the instantiated virtual terminal.

    Its value is a tuple of the form (columns, lines) and it can be parametrized by
    using `with_terminal_size` decorator or `@pytest.mark.parametrize` with indirect flag.

    If it's not parametrized, the terminal will be instantiated with size (80, 24)
    """
    if hasattr(request, "param"):
        return request.param

    return (80, 24)


@pytest.fixture(name="tuitest_env")
def fixture_tuitest_env(request):
    """Fixture that determines the environment variables available to the process.

    It can be parametrized by using `with_env decorator` or `@pytest.mark.parametrize`
    with indirect flag. If it's not parametrized, only the default environment variables
    will be used.
    """
    if hasattr(request, "param"):
        return request.param

    return None
###############################################################################
# Decorators
###############################################################################


def test_executable(executable: str):
    """Use this executable for the test.

    Note: This is a decorator intended to be applied to a test function.
    """
    return pytest.mark.parametrize("tuitest_executable", [executable], indirect=True)


def with_arguments(args: list[str]):
    """Send these arguments to the executable.

    Note: This is a decorator intended to be applied to a test function."""
    return pytest.mark.parametrize("tuitest_arguments", [args], indirect=True)


def with_captured_stdout(capture_output: bool = True):
    """Capture stdout instead of showing it in the virtual terminal.

    The captured stdout is available in the output of
    `pytest_tuitest.terminal.Terminal.wait_for_finished`.

    Note: This is a decorator intended to be applied to a test function.

    Args:
        capture_output: Whether the output should be captured.
    """
    return pytest.mark.parametrize("tuitest_capture_stdout", [capture_output], indirect=True)


def with_captured_stderr(capture_stderr: bool = True):
    """Capture stderr instead of showing it in the virtual terminal.

    The captured stderr is available in the output of
    `pytest_tuitest.terminal.Terminal.wait_for_finished`.

    Note: This is a decorator intended to be applied to a test function.

    Args:
        capture_stderr: Whether the stderr output should be captured.
    """
    return pytest.mark.parametrize("tuitest_capture_stderr", [capture_stderr], indirect=True)


def with_stdin(stdin: str):
    """Send the provided stdin to the executable stdin.

    Note: This is a decorator intended to be applied to a test function.

    Args:
        stdin: UTF8 encoded string to send to the executable
    """
    return pytest.mark.parametrize("tuitest_stdin", [stdin], indirect=True)


def with_terminal_size(columns: int, lines: int):
    """Initialize the terminal with the provided size.

    Note: This is a decorator intended to be applied to a test function.

    Args:
        columns: The number of columns in the virtual terminal.
        lines: The number of lines in the virtual terminal.
    """
    return pytest.mark.parametrize("tuitest_terminal_size", [(columns, lines)], indirect=True)


def with_env(env: dict[str, str]):
    """Run the process with the provided environment variables.

    Args:
        env: The environment variables to be use with the process.
             If a variable already exists, it will be overwritten.
    """
    return pytest.mark.parametrize("tuitest_env", [env], indirect=True)
