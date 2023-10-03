"""Classes for handling and communication with processes in pseudo terminals."""
import errno
import fcntl
import os
import pty
import struct
import termios
from select import select


class ProcessFinished(Exception):
    """The process has finished finished."""

# The fact that columns and lines, as well as stdout and stderr, come in pairs
# increases the neccessary number of arguments/attributes. At its present state,
# this should be OK. Needs to be reconsidered if the number of arguments increases.


class Process:  # pylint: disable=too-many-instance-attributes
    """A class repsesenting a process executing in a pseudo terminal."""

    # pylint: disable-next=too-many-arguments
    def __init__(self,
                 executable: str,
                 args: list[str] = None,
                 columns: int = 80,
                 lines: int = 24,
                 capture_stdout: bool = False,
                 capture_stderr: bool = False) -> None:
        """Initialize a Process object

        Args:
            executable (str): Executable to run. Must be either full path or present in path.
            args (list[str], optional): List of arguments to send to the process. If not provided
                an empty list is used.
            columns (int, optional): Width of the pseudo terminal. Defaults to 80.
            lines (int, optional): Height of the pseudo terminal. Defaults to 24.
            capture_stdout (bool, optional): If this is set to true, stdout will not be returned
                as part of get_new_output and will be captured instead. The captured output will
                be available once the process finishes. See wait_for_finished.
                Useful for testing applications that write on /dev/tty.
            capture_stderr (bool, optional): If this is set to true, stderr will not be returned
                as part of get_new_output and will be captured instead. The captured output will
                be available once the process finishes. See wait_for_finished.
                Useful for testing applications that write on /dev/tty.
        """
        if not args:
            args = []

        self._lines = lines
        self._columns = columns
        self._captured_stdout = None
        self._captured_stderr = None
        self._exit_status = None

        if capture_stdout:
            self._child_stdout_r, stdout_w = os.pipe2(os.O_NONBLOCK)
        else:
            self._child_stdout_r, stdout_w = (None, None)

        if capture_stderr:
            self._child_stderr_r, stderr_w = os.pipe2(os.O_NONBLOCK)
        else:
            self._child_stderr_r, stderr_w = (None, None)

        self._child_pid, self._child_fd = pty.fork()

        # Parent and child will continue executing the same code
        # but get different return values. Parent gets the actual
        # pid of the child, while the child gets zero.
        if self._child_pid == 0:
            env = {
                "TERM": "linux",
                "COLUMNS": str(columns),
                "LINES": str(lines),
            }

            if self._child_stdout_r is not None:
                os.close(self._child_stdout_r)
                os.dup2(stdout_w, 1)

            if self._child_stderr_r is not None:
                os.close(self._child_stderr_r)
                os.dup2(stderr_w, 2)

            # This replaces the python process in child
            os.execvpe(executable, [executable, *args], env=env)

        if stdout_w is not None:
            os.close(stdout_w)

        if stderr_w is not None:
            os.close(stderr_w)

        # See "man ioctl_tty for details"
        terminal_size = struct.pack('HHHH', lines, columns, 0, 0)
        fcntl.ioctl(self._child_fd, termios.TIOCSWINSZ, terminal_size)

        os.set_blocking(self._child_fd, False)

    def _update_captured_stds(self):
        def read_all(file_descriptor):
            ret = b""
            max_read_size = 1024

            while True:
                data = os.read(file_descriptor, max_read_size)

                if data == b"":
                    return ret

                ret += data

        if self._child_stdout_r is not None and self._captured_stdout is None:
            self._captured_stdout = read_all(self._child_stdout_r)

        if self._child_stderr_r is not None and self._captured_stderr is None:
            self._captured_stderr = read_all(self._child_stderr_r)

    def get_new_output(self, max_size: int = 1024) -> bytes:
        """Get any output generated inside the terminal after the last call to this function.

        Args:
            max_size (int, optional): Maximum amount of data to return. Defaults to 1024.

        Raises:
            ProcessFinished: If the process has finished and there is no more output to read.

        Returns:
            bytes: The output generated by the process.
        """
        # End of file signalling seems to be platform dependent and could
        # either be an empty value or an IO error. Hard to find any
        # reasonable source confirming this. The best I could find:
        # https://github.com/pexpect/pexpect/blob/6e2bbd5568fb8468c176c2c9b7f20d4f4bf7dd71/pexpect/spawnbase.py#L182
        # https://stackoverflow.com/questions/10238298/ruby-on-linux-pty-goes-away-without-eof-raises-errnoeio
        # So, essentially, handle both as an EOF.
        try:
            data = os.read(self._child_fd, max_size)
        except BlockingIOError:
            return b""
        except OSError as e:
            if e.args[0] == errno.EIO:
                # End of file reached, original error irrelevant
                # pylint: disable-next=raise-missing-from
                raise ProcessFinished()

        if not data:
            raise ProcessFinished()

        return data

    def write(self, bytes_to_write: bytes) -> None:
        """Write the provided bytes to the process's stdin.

        Args:
            bytes_to_write (bytes): The bytes to write.
        """
        os.write(self._child_fd, bytes_to_write)

    def wait_for_output(self, timeout_sec: float = None) -> bool:
        """Block until new output is received from the executable.

        Args:
            timeout_sec (float, optional): If provided, maximuma amount of time
            to wait for new output. Defaults to None.

        Returns:
            bool: True if new output has been received, False otherwise. Note that
                this method can only return True if timeout_sec is not given.
        """
        readable, _, _ = select([self._child_fd], [], [], timeout_sec)
        return bool(readable)

    def wait_for_finished(self) -> tuple[int, bytes, bytes]:
        """Block until the process finishes and return the information about it.

        If the process has already finished, directly returns the appropriate values.

        Returns:
            tuple[int, bytes, bytes]: Tuple with three elements:
                - Process exit status
                - Captured stdout if capture_stdout was True in init
                - Captured stderr if capture_stderr was True in init
        """

        # Process already finished and everything already set
        if self._exit_status is not None:
            return (self._exit_status, self._captured_stdout, self._captured_stderr)

        # Note: This only handles processes that exited gracefully and were not
        # forcefully stopped.
        _, exit_status_indication = os.waitpid(self._child_pid, os.WUNTRACED)

        self._exit_status = exit_status_indication >> 8
        self._update_captured_stds()

        return (self._exit_status, self._captured_stdout, self._captured_stderr)

    @property
    def lines(self) -> int:
        """Number of lines in the pseudo terminal.

        Returns:
            int: Number of lines in the pseudo terminal.
        """
        return self._lines

    @property
    def columns(self) -> int:
        """Number of columns in the pseudo terminal.

        Returns:
            int: Number of columns in the pseudo terminal.
        """
        return self._columns
