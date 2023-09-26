"""Module for virtual terminal interaction."""
import pyte

from .colors import ColorNamed
from .process import Process, ProcessFinished


class OutsideBounds(Exception):
    """Raised when information is requested for invalid coordinates."""


class UnsupportedColor(Exception):
    """Raised when a color cannot be decoded."""


_PYTE_TO_COLOR_NAMED_MAP = {
    "black": ColorNamed.BLACK,
    "red": ColorNamed.RED,
    "green": ColorNamed.GREEN,
    "brown": ColorNamed.YELLOW,
    "blue": ColorNamed.BLUE,
    "magenta": ColorNamed.MAGENTA,
    "cyan": ColorNamed.CYAN,
    "white": ColorNamed.WHITE,
    "brightblack": ColorNamed.BRIGHT_BLACK,
    "brightred": ColorNamed.BRIGHT_RED,
    "brightgreen": ColorNamed.BRIGHT_GREEN,
    "brightbrown": ColorNamed.BRIGHT_BROWN,
    "brightblue": ColorNamed.BRIGHT_BLUE,
    "brightmagenta": ColorNamed.BRIGHT_MAGENTA,
    "brightcyan": ColorNamed.BRIGHT_CYAN,
    "brightwhite": ColorNamed.BRIGHT_WHITE,
    "default": ColorNamed.DEFAULT,
}


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

    def get_foreground_at(self, line: int, column: int) -> ColorNamed:
        """Get the foreground color at given coordinates.

        Args:
            line (int): The line at which to get the color.
            column (int): The column at which to get the color.

        Returns:
            ColorNamed: Color at the given coordinates.
        """
        self._update_screen()

        msg = (f"Coordinates ({line}, {column}) are invalid for terminal size"
               f" {self._process.lines}x{self._process.columns}")
        self._raise_if_outside_bounds(line, column, msg)

        pyte_color = self._screen.buffer[line][column].fg

        if pyte_color not in _PYTE_TO_COLOR_NAMED_MAP:
            msg = f"Could not decode color at ({line}, {column})"
            raise UnsupportedColor(msg)

        return _PYTE_TO_COLOR_NAMED_MAP[pyte_color]

    def wait_for_output(self) -> None:
        """Block until new output is received from the process."""
        self._process.wait_for_output()

    def wait_for_finished(self) -> tuple[int, bytes, bytes]:
        """Block until the process finishes and return the information about it.

        This is just a proxy method to wait_for_finished of the inner process.
        """
        return self._process.wait_for_finished()

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

    def _raise_if_outside_bounds(self, line, column, msg) -> None:
        """Raise OutsideBounds exception if given coordinates are not inside the terminal."""
        if line < 0 or line >= self._process.lines:
            raise OutsideBounds(msg)

        if column < 0 or column >= self._process.columns:
            raise OutsideBounds(msg)
