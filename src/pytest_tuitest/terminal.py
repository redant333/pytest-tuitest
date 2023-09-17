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

    def get_char_at(self, line: int, column: int) -> str:
        """Get the character at the given coordinates in the terminal.

        Args:
            line (int): Line from which to get the char (zero indexed)
            column (int): Column from which to get the char (zero indexed)

        Raises:
            OutsideBounds: If the given coordinates are not inside the terminal.

        Returns:
            str: Character at the given coordinates. If nothing is present,
                " " is returned.
        """
        line_outside = line < 0 or line >= self._process.lines
        column_outside = column < 0 or column >= self._process.columns

        if line_outside or column_outside:
            msg = (f"Requested location ({line}, {column}) is outside "
                   f"terminal with size {self._process.lines}x{self._process.columns}")
            raise OutsideBounds(msg)

        self._update_screen()
        return self._screen.buffer[line][column].data

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
