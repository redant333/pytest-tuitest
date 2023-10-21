"""Tests for Process class."""
import pytest

from pytest_tuitest import Process, ProcessFinished


def get_all_output(process: Process) -> bytes:
    """Read the process output until it finishes.

    Args:
        process (Process): The process whose output should be read.

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

    @pytest.mark.parametrize("exit_status", [0, 5])
    def test_wait_for_finished_returns_correct_exit_status(self, exit_status):
        """Verify that the exit status of the process is correctly captured."""
        process = Process("sh", ["-c", f"exit {exit_status}"])

        returned_status, _, _ = process.wait_for_finished()

        msg = f"Expected exit status {exit_status}, got {returned_status}"
        assert returned_status == exit_status, msg

    def test_wait_for_finished_blocks_until_the_process_finishes(self):
        """Verify that the exit status is reported as None if the process has not yet finished."""
        exit_status = 3
        process = Process("sh", ["-c", "sleep 1 && return 3"])

        # This will be executed before the 1s elapses
        returned_status, _, _ = process.wait_for_finished()

        msg = f"Expected exit status {exit_status}, got {returned_status}"
        assert returned_status == exit_status, msg

    def test_wait_for_finished_returns_none_for_captured_stdout_when_not_requested(
            self, test_scripts_dir):
        """Verify that None is returned for stdout and stderr when they are not captured."""
        outputs_script = test_scripts_dir / "outputs.sh"
        process = Process(str(outputs_script))

        exit_status, stdout, stderr = process.wait_for_finished()

        msg = "Process failed unexpectedly while running outputs.sh"
        assert exit_status == 0, msg

        msg = f"Unexpected value {stdout} returned for uncaptured stdout"
        assert stdout is None, msg

        msg = f"Unexpected value {stderr} returned for uncaptured stderr"
        assert stderr is None, msg

    def test_wait_for_finished_stdout_correctly_captured_when_requested(self, test_scripts_dir):
        """Verify that stdout is correctly captured when requested."""
        outputs_script = test_scripts_dir / "outputs.sh"
        process = Process(str(outputs_script), capture_stdout=True)

        exit_status, stdout, stderr = process.wait_for_finished()

        msg = "Process failed unexpectedly while running outputs.sh"
        assert exit_status == 0, msg

        expected = b"This goes to stdout\n"
        msg = f"Unexpected value {stdout} returned for stdout, expected {expected}"
        assert stdout == expected, msg

        msg = f"Unexpected value {stderr} returned for uncaptured stderr"
        assert stderr is None, msg

    def test_wait_for_finished_stderr_correctly_captured_when_requested(self, test_scripts_dir):
        """Verify that stderr is correctly captured when requested."""
        outputs_script = test_scripts_dir / "outputs.sh"
        process = Process(str(outputs_script), capture_stderr=True)

        exit_status, stdout, stderr = process.wait_for_finished()

        msg = "Process failed unexpectedly while running outputs.sh"
        assert exit_status == 0, msg

        msg = f"Unexpected value {stdout} returned for uncaptured stdout"
        assert stdout is None, msg

        expected = b"This goes to stderr\n"
        msg = f"Unexpected value {stderr} returned for stderr, expected {expected}"
        assert stderr == expected, msg

    # This will fail as long as pipes are used to buffer the captured stdout
    @pytest.mark.xfail
    def test_wait_for_finished_stdout_correctly_captured_for_long_output(self):
        """Verify that stdout can be captured even if contains large amount of data."""
        character_count = 1024 * 1024  # 1MiB
        process = Process("bash",
                          ["-c", f"yes | head -c {character_count}"],
                          capture_stdout=True)

        exit_status, stdout, _ = process.wait_for_finished()

        msg = "Process failed unexpectedly"
        assert exit_status == 0, msg

        msg = f"Got {len(stdout)} bytes, expected {character_count}"
        assert len(stdout) == character_count, msg

    # This will fail as long as pipes are used to buffer the captured stdout
    @pytest.mark.xfail
    def test_wait_for_finished_stderr_correctly_captured_for_long_output(self):
        """Verify that stdout can be captured even if contains large amount of data."""
        character_count = 1024 * 1024  # 1MiB
        process = Process("bash",
                          ["-c", f"yes | head -c {character_count} >&2"],
                          capture_stderr=True)

        exit_status, _, stderr = process.wait_for_finished()

        msg = "Process failed unexpectedly"
        assert exit_status == 0, msg

        msg = f"Got {len(stderr)} bytes, expected {character_count}"
        assert len(stderr) == character_count, msg

    def test_specified_stdin_is_correctly_delivered_to_the_process(self):
        """Verify that the specified stdin is piped into the executable."""
        stdin = b"this is a test"
        process = Process("wc", ["-c"], stdin=stdin)

        output = get_all_output(process)

        expected_output = f"{len(stdin)}\r\n".encode()
        msg = f"Got output {output}, expected {expected_output}"
        assert output == expected_output, msg

    def test_eof_in_stdin_can_be_detected(self):
        """Verify that the process detects EOF in the delivered stdin.

        Command cat will not finish if it does not detect EOF.
        """
        stdin = b"test"
        process = Process("cat", stdin=stdin)
        exit_code, _, _ = process.wait_for_finished()

        assert exit_code == 0, "Process failed unexpectedly"
