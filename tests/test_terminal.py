"""Tests for Terminal class."""
import time

import pytest

from pytest_tuitest import (ColorNamed, OutsideBounds, Process, Terminal,
                            TimedOut, UnsupportedColor)

# These are test classes. There use is only for organization so the
# number of public methods does not matter.
# pylint: disable=too-few-public-methods


@pytest.fixture(name="terminal")
def create_terminal(request, test_scripts_dir) -> Terminal:
    """Create a Terminal instance.

    This fixture creates a Terminal instance from the parameters that can
    be set with pytest.mark.parametrize. It expects a dictionary with the
    following keys: "executable", "lines", "columns". If "lines" is omitted
    24 is used instead. If columns is omitted, 80 is used instead.
    """
    executable = test_scripts_dir / request.param["executable"]
    lines = request.param.get("lines", 24)
    columns = request.param.get("columns", 80)

    stdin = request.param.get("stdin", None)
    if stdin:
        stdin = stdin.encode()
    capture_stdout = request.param.get("capture_stdout", False)
    capture_stderr = request.param.get("capture_stderr", False)
    args = request.param.get("args", [])

    process = Process(str(executable), args=args, columns=columns, lines=lines, stdin=stdin,
                      capture_stdout=capture_stdout, capture_stderr=capture_stderr)
    return Terminal(process)


class TestGetStringAt:
    """Tests for Terminal.get_string_at."""
    @pytest.mark.parametrize("terminal", [{"executable": "colors.sh"}], indirect=True)
    @pytest.mark.parametrize("line, column, length, expected", [
        (0, 0, 2, "16"),
        (1, 8, 10, "background"),
        (5, 0, 80, "Default background | Red foreground" + " " * 45),
    ])
    # pylint: disable-next=too-many-arguments
    def test_returns_expected_value_when_inside_bounds(
            self, terminal, line, column, length, expected):
        """Verify that the expected value is returned for valid coordinates."""
        terminal.wait_for_output()
        string = terminal.get_string_at(line, column, length)

        msg = f"Got string '{string}', expected '{expected}'"
        assert string == expected, msg

    @pytest.mark.parametrize("terminal",
                             [{"executable": "colors.sh", "lines": 10, "columns": 10}],
                             indirect=True)
    @pytest.mark.parametrize("line, column, length", [
        (5, 10, 1),
        (10, 5, 1),
        (10, 10, 1),
        (-1, 5, 1),
        (5, -1, 1),
        (-1, -1, 1),
        (5, 8, 3),
        (5, 5, -1),
        (5, 5, 0),
    ])
    def test_raises_an_exception_when_outside_bounds(self, terminal, line, column, length):
        """Verify that an exception is raised for invalid coordinates."""
        with pytest.raises(OutsideBounds):
            terminal.get_string_at(line, column, length)


class TestWaitForFinished:
    """Tests for Termina.wait_for_finished."""
    @pytest.mark.parametrize("terminal",
                             [{
                                 "executable": "outputs.sh",
                                 "capture_stdout": True,
                                 "capture_stderr": True}],
                             indirect=True)
    def test_returns_all_values_as_expected_when_capturing(self, terminal):
        """Verify that all expected values are returned when capturing."""
        exit_code, stdout, stderr = terminal.wait_for_finished()

        msg = "Process unexpectedly failed"
        assert exit_code == 0, msg

        expected = b"This goes to stdout\n"
        msg = f"Got '{stdout}' as stdout, expected '{expected}'"
        assert stdout == expected, msg

        expected = b"This goes to stderr\n"
        msg = f"Got '{stderr}' as stderr, expected '{expected}'"
        assert stderr == expected, msg

    @pytest.mark.parametrize("terminal",
                             [{
                                 "executable": "outputs.sh",
                                 "capture_stdout": False,
                                 "capture_stderr": False}],
                             indirect=True)
    def test_returns_none_for_stds_when_not_capturing(self, terminal):
        """Verify None is returned for stdout and stderr when not capturing."""
        exit_code, stdout, stderr = terminal.wait_for_finished()

        msg = "Process unexpectedly failed"
        assert exit_code == 0, msg

        msg = f"Got '{stdout}' as stdout, expected None"
        assert stdout is None, msg

        msg = f"Got '{stderr}' as stderr, expected None"
        assert stderr is None, msg


class TestGetForegroundAt:
    """Tests for Terminal.get_foreground_at."""

    @pytest.mark.parametrize("terminal", [{"executable": "all_16_colors.sh"}], indirect=True)
    @pytest.mark.parametrize("line, expected_color", [
        (0, ColorNamed.BLACK),
        (1, ColorNamed.RED),
        (2, ColorNamed.GREEN),
        (3, ColorNamed.YELLOW),
        (4, ColorNamed.BLUE),
        (5, ColorNamed.MAGENTA),
        (6, ColorNamed.CYAN),
        (7, ColorNamed.WHITE),
        (8, ColorNamed.BRIGHT_BLACK),
        (9, ColorNamed.BRIGHT_RED),
        (10, ColorNamed.BRIGHT_GREEN),
        (11, ColorNamed.BRIGHT_YELLOW),
        (12, ColorNamed.BRIGHT_BLUE),
        (13, ColorNamed.BRIGHT_MAGENTA),
        (14, ColorNamed.BRIGHT_CYAN),
        (15, ColorNamed.BRIGHT_WHITE),
        (16, ColorNamed.DEFAULT),
    ])
    def test_returns_correct_16_color(self, terminal, line, expected_color):
        """Verify that foreground color is returned as expected."""
        terminal.wait_for_output()

        color = terminal.get_foreground_at(line, 0)

        assert color == expected_color

    @pytest.mark.parametrize("terminal", [{"executable": "colors.sh"}], indirect=True)
    def test_raises_exception_for_256_color(self, terminal):
        """Verify that an exception is raised when getting a color from 256 color set.

        Currently, only colors from 16 color set are supported.
        """
        terminal.wait_for_output()

        with pytest.raises(UnsupportedColor):
            terminal.get_foreground_at(7, 0)

    @pytest.mark.parametrize("terminal",
                             [{"executable": "colors.sh", "lines": 10, "columns": 10}],
                             indirect=True)
    @pytest.mark.parametrize("line, column", [
        (5, 10),
        (10, 5),
        (10, 10),
        (-1, 5),
        (5, -1),
        (-1, -1),
    ])
    def test_raises_exception_for_coordinates_outside_bounds(self, terminal, line, column):
        """Verify that an exception is raised for coordinates outside the terminal."""
        with pytest.raises(OutsideBounds):
            terminal.get_foreground_at(line, column)


class TestGetBackgroundAt:
    """Tests for Terminal.get_background_at."""

    @pytest.mark.parametrize("terminal", [{"executable": "all_16_colors.sh"}], indirect=True)
    @pytest.mark.parametrize("line, expected_color", [
        (0, ColorNamed.BLACK),
        (1, ColorNamed.RED),
        (2, ColorNamed.GREEN),
        (3, ColorNamed.YELLOW),
        (4, ColorNamed.BLUE),
        (5, ColorNamed.MAGENTA),
        (6, ColorNamed.CYAN),
        (7, ColorNamed.WHITE),
        (8, ColorNamed.BRIGHT_BLACK),
        (9, ColorNamed.BRIGHT_RED),
        (10, ColorNamed.BRIGHT_GREEN),
        (11, ColorNamed.BRIGHT_YELLOW),
        (12, ColorNamed.BRIGHT_BLUE),
        (13, ColorNamed.BRIGHT_MAGENTA),
        (14, ColorNamed.BRIGHT_CYAN),
        (15, ColorNamed.BRIGHT_WHITE),
        (16, ColorNamed.DEFAULT),
    ])
    def test_returns_correct_16_color(self, terminal, line, expected_color):
        """Verify that foreground color is returned as expected."""
        terminal.wait_for_output()

        color = terminal.get_background_at(line, 14)

        assert color == expected_color

    @pytest.mark.parametrize("terminal", [{"executable": "colors.sh"}], indirect=True)
    def test_raises_exception_for_256_color(self, terminal):
        """Verify that an exception is raised when getting a color from 256 color set.

        Currently, only colors from 16 color set are supported.
        """
        terminal.wait_for_output()

        with pytest.raises(UnsupportedColor):
            terminal.get_background_at(7, 0)

    @pytest.mark.parametrize("terminal",
                             [{"executable": "colors.sh", "lines": 10, "columns": 10}],
                             indirect=True)
    @pytest.mark.parametrize("line, column", [
        (5, 10),
        (10, 5),
        (10, 10),
        (-1, 5),
        (5, -1),
        (-1, -1),
    ])
    def test_raises_exception_for_coordinates_outside_bounds(self, terminal, line, column):
        """Verify that an exception is raised for coordinates outside the terminal."""
        with pytest.raises(OutsideBounds):
            terminal.get_background_at(line, column)


class TestWaitForStableOutput:
    """Tests for Terminal.wait_for_stable_output."""
    @pytest.mark.parametrize("terminal", [{"executable": "reversing_echo.sh"}], indirect=True)
    def test_waits_at_least_given_number_of_seconds_for_running_process(self, terminal):
        """Verify that it takes at least stable_time to determine that the output is stable."""
        stable_time = 2

        before = time.time()
        terminal.wait_for_stable_output(stable_time)
        after = time.time()

        time_elapsed = after - before
        tolerance_sec = 0.01  # Slight difference is expected

        msg = f"Expected to take {stable_time}s, actually took {time_elapsed}s"
        assert time_elapsed == pytest.approx(
            stable_time, rel=tolerance_sec), msg

    @pytest.mark.parametrize("terminal", [{"executable": "spammy.sh"}], indirect=True)
    @pytest.mark.skip("Flaky results, the exception is not always thrown.")
    def test_raises_an_exception_if_terminal_does_not_stabilize(self, terminal):
        """Verify that an exception is raised if the terminal does not stabilize."""
        max_wait_time = 3

        before = time.time()

        with pytest.raises(TimedOut):
            terminal.wait_for_stable_output(max_wait_sec=max_wait_time)

        after = time.time()

        time_elapsed = after - before
        tolerance_sec = 0.01  # Slight difference is expected

        msg = f"Expected to time out after {max_wait_time}, timed out after {time_elapsed}"
        assert time_elapsed == pytest.approx(
            max_wait_time, rel=tolerance_sec), msg

    @pytest.mark.parametrize("terminal", [{"executable": "colors.sh"}], indirect=True)
    def test_returns_instantly_for_a_finished_process(self, terminal):
        """Verify that finished process is considered already stable.

        This means the method returns immediately.
        """
        stable_time = 2

        terminal.wait_for_output()

        before = time.time()
        terminal.wait_for_stable_output(stable_time)
        after = time.time()

        time_elapsed = after - before
        very_short = 0.01

        msg = f"Expected to return immediately, actually took {time_elapsed}s"
        assert time_elapsed < very_short, msg


class TestSend:
    """Tests for Terminal.send."""

    @pytest.mark.parametrize("terminal", [{"executable": "reversing_echo.sh"}], indirect=True)
    def test_successfully_interacts_with_terminal(self, terminal):
        """Verify that it's possible to send a simple line to the terminal stdin."""
        text_to_enter = "stuff"
        expected_echo = "ffuts"

        terminal.send(text_to_enter + "\n")
        terminal.wait_for_stable_output()

        string = terminal.get_string_at(0, 0, len(text_to_enter))
        assert string == text_to_enter, f"Could not get the entered text, got '{string}'"

        string = terminal.get_string_at(1, 0, len(expected_echo))
        assert string == expected_echo, f"Could not get the echo, got '{string}'"


class TestStdin:
    """Tests for interaction with Process with piped stdin."""
    @pytest.mark.parametrize("terminal", [{"executable": "run_command.sh",
                                           "args": ["less"],
                                           "stdin": "things\nstuff"}],
                             indirect=True)
    def test_interaction_with_specified_stdin(self, terminal):
        """Verify the interaction with the underlying process is possible with specified stdin.

        Specifying stdin should not prevent the process from reading /dev/tty.
        """
        first_line = "things"
        second_line = "stuff"

        terminal.wait_for_stable_output()

        msg = "Top line before search not as expected"
        assert terminal.get_string_at(0, 0, len(first_line)) == first_line, msg

        # Initiate a search in less that will bring the second line to the top
        terminal.send(f"/{second_line}\n")
        terminal.wait_for_stable_output()

        msg = "Top line after search not as expected"
        top_line = terminal.get_string_at(0, 0, len(second_line))
        assert top_line == second_line, msg
