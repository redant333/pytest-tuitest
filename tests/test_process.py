"""Tests for Process class."""
from pytest_tuitest import Process, ProcessFinished


def get_all_output(process: Process) -> bytes:
    """Read the process output until it finishes.

    Args:
        process (Process): The process whose output shoudl be read.

    Returns:
        bytes: The read output.
    """
    output = b""

    while True:
        try:
            output += process.get_new_output()
        except ProcessFinished:
            break

    return output


class TestProcess:
    """Tests for Process class."""

    def test_returns_complete_output_for_simple_command(self):
        """Verify that the output is as expected with simple echo command."""
        process = Process("sh", ["-c", "echo test"])

        output = get_all_output(process)

        expected_output = b"test\r\n"
        msg = f"Got output {output}, expected {expected_output}"
        assert output == expected_output, msg

    def test_sets_terminal_size_environment_variables(self):
        """Verify that Process sets terminal size environment variables."""
        width = 10
        height = 15

        args = ["-c", 'echo "$COLUMNS $LINES"']
        process = Process("sh", args, columns=width, lines=height)

        output = get_all_output(process)

        expected_output = f"{width} {height}\r\n".encode()

        msg = f"Got terminal size {output}, expected {expected_output}"
        assert output == expected_output, msg

    def test_sets_ioctl_terminal_size(self):
        """Verify that Process sets terminal size through IO control.

        Python os.get_terminal_size uses this method to get the terminal size
        and ignores environment variables.
        """
        width = 10
        height = 15

        args = ["-c", ("from os import get_terminal_size;"
                       "print(get_terminal_size().columns, get_terminal_size().lines)")]
        process = Process("python3", args, columns=width, lines=height)

        output = get_all_output(process)

        expected_output = f"{width} {height}\r\n".encode()

        msg = f"Got terminal size {output}, expected {expected_output}"
        assert output == expected_output, msg
