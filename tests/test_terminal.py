"""Tests for Terminal class."""
import pytest

from pytest_tuitest import OutsideBounds, Process, Terminal


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

    process = Process(str(executable), columns=columns, lines=lines)
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
