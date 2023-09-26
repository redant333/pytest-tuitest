"""Tests for Terminal class."""
import pytest

from pytest_tuitest import (ColorNamed, OutsideBounds, Process, Terminal,
                            UnsupportedColor)


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
    capture_stdout = request.param.get("capture_stdout", False)
    capture_stderr = request.param.get("capture_stderr", False)

    process = Process(str(executable), columns=columns, lines=lines,
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
