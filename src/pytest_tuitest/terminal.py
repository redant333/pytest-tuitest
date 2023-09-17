"""Module for virtual terminal interaction."""
import pyte

from .process import Process, ProcessFinished


class OutsideBounds(Exception):
    """Raised when information is requested for invalid coordinates."""


class Terminal:
    """A class for terminal emulation and interaction."""

    def __init__(self, process: Process) -> None:
        """Initialize a Terminal object.

        Args:
            process (Process): The process to execute in this virtual terminal.
        """
        self._screen = pyte.Screen(process.columns, process.lines)
        self._stream = pyte.ByteStream(self._screen)
        self._process = process

    def get_string_at(self, line: int, column: int, length: int) -> str:
        """Get the string of given length at the given coordiantes in the terminal.

        This method only supports getting a string that is completely located on
        one line. For locations without any text, this method uses ' '.

        Args:
            line (int): Line where the string starts (zero indexed).
            column (int): Column where the string starts (zero indexed).
            length (int): Length of the string.

        Raises:
            OutsideBounds: If the string is not completely located within the
                terminal bounds.

        Returns:
            str: The requested string.
        """
        # Check if any of the arguments are invalid
        column_start_outside = column < 0 or column >= self._process.columns

        column_end = column + length - 1
        column_end_outside = column_end < 0 or column_end >= self._process.columns

        line_outside = line < 0 or line >= self._process.lines

        length_invalid = length <= 0

        if column_start_outside or column_end_outside or line_outside or length_invalid:
            msg = (f"Requested length {length} at location ({line}, {column})"
                   " is not valid for terminal size "
                   f"{self._process.lines}x{self._process.columns}")
            raise OutsideBounds(msg)

        # All arguments good, retrieve the string
        self._update_screen()
        chars = [self._screen.buffer[line][column + offset].data
                 for offset in range(0, length)]

        return "".join(chars)

    def wait_for_output(self) -> None:
        """Block until new output is received from the process."""
        self._process.wait_for_output()

    def _update_screen(self) -> None:
        """Refresh the internal knowledge about the process output."""
        while True:
            try:
                data = self._process.get_new_output()

                if not data:
                    break

                self._stream.feed(data)
            except ProcessFinished:
                break
