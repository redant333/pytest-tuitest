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


class TestGetCharAt:
    """Tests for Terminal.get_char_at."""
    @pytest.mark.parametrize("terminal", [{"executable": "colors.sh"}], indirect=True)
    @pytest.mark.parametrize("line, column, expected", [
        (0, 0, "1"),
        (1, 2, "f"),
        (5, 2, "f"),
        (0, 50, " "),
    ])
    def test_returns_expected_value_when_inside_bounds(self, terminal, line, column, expected):
        """Verify that the expected value is returned for valid coordinates."""
        terminal.wait_for_output()
        char = terminal.get_char_at(line, column)

        msg = f"Got char '{char}', expected '{expected}'"
        assert char == expected, msg

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
    def test_raises_an_exception_when_outside_bounds(self, terminal, line, column):
        """Verify that an exception is raised for invalid coordinates."""
        with pytest.raises(OutsideBounds):
            terminal.get_char_at(line, column)
