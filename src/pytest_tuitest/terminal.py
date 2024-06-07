"""Module for virtual terminal interaction."""
import time

import pyte

from .colors import ColorNamed
from .process import Process, ProcessFinished


class OutsideBounds(Exception):
    """Raised when information is requested for invalid coordinates."""


class TimedOut(Exception):
    """Raised when an operation times out."""


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
    "brightbrown": ColorNamed.BRIGHT_YELLOW,
    "brightblue": ColorNamed.BRIGHT_BLUE,
    "brightmagenta": ColorNamed.BRIGHT_MAGENTA,
    # pyte typo for background colors
    "bfightmagenta": ColorNamed.BRIGHT_MAGENTA,
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
        self._process_running = True

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
        pyte_color = self._get_attribute_at(line, column, "fg")

        if pyte_color not in _PYTE_TO_COLOR_NAMED_MAP:
            return ColorNamed.COULD_NOT_DECODE

        return _PYTE_TO_COLOR_NAMED_MAP[pyte_color]

    def get_background_at(self, line: int, column: int) -> ColorNamed:
        """Get the background color at given coordinates.

        Args:
            line (int): The line at which to get the color.
            column (int): The column at which to get the color.

        Returns:
            ColorNamed: Color at the given coordinates.
        """
        pyte_color = self._get_attribute_at(line, column, "bg")

        if pyte_color not in _PYTE_TO_COLOR_NAMED_MAP:
            return ColorNamed.COULD_NOT_DECODE

        return _PYTE_TO_COLOR_NAMED_MAP[pyte_color]

    def wait_for_output(self) -> None:
        """Block until new output is received from the process."""
        self._process.wait_for_output()

    def wait_for_finished(self, encoding: str = "utf8") -> tuple[int, str, str]:
        """Block until the process finishes and return the information about it.

        Args:
            encoding (str): The encoding to be used to decode captured outputs.

        Returns:
            tuple[int, str, str]: A tuple with the following information about the process:
                - return code of the process
                - captured stdout if stdout capturing is enabled, None otherwise
                - captured stderr if stderr capturing is enabled, None otherwise
        """
        (status, stdout, stderr) = self._process.wait_for_finished()

        if stdout is not None:
            stdout = stdout.decode(encoding)

        if stderr is not None:
            stderr = stderr.decode(encoding)

        return (status, stdout, stderr)

    def wait_for_stable_output(self, stable_time_sec=0.1, max_wait_sec=5) -> None:
        """Wait for the terminal output to stabilize for at least stable_time_sec.

        Useful for making sure operations that produce multiple lines are fully
        finished before continuing.

        Args:
            stable_time_sec (float, optional): The terminal is considered stable
                after it remains unchanged for this amount of time. Defaults to 0.1.
            max_wait_sec (int, optional): Maximum amount of time to wait for the
                terminal to become stable. Defaults to 5.

        Raises:
            TimedOut: When the terminal doesn't stabilize within max_wait_sec.
        """
        self._update_screen()
        started = time.time()
        last_update = time.time()

        def should_poll():
            # Nothing is going to change if the process has finished
            if not self._process_running:
                return False

            now = time.time()
            elapsed_from_update = now - last_update
            if elapsed_from_update >= stable_time_sec:
                return False

            elapsed_from_start = now - started
            if elapsed_from_start > max_wait_sec:
                raise TimedOut()

            return True

        while should_poll():
            output_ready = self._process.wait_for_output(timeout_sec=0.01)
            if not output_ready:
                continue

            screen_updated = self._update_screen()
            if screen_updated:
                last_update = time.time()

    def send(self, characters: str) -> None:
        """Send the provided characters to the process's stdin.

        Args:
            characters (str): The characters to send.
        """
        encoded = characters.encode()
        self._process.write(encoded)

    def _update_screen(self) -> bool:
        """Refresh the internal knowledge about the process output.

        Returns:
            (bool): True if the screen has changed, False otherwise.
        """
        screen_updated = False

        while self._process_running:
            try:
                data = self._process.get_new_output()

                if not data:
                    break

                self._stream.feed(data)
                screen_updated = True
            except ProcessFinished:
                self._process_running = False
                break

        return screen_updated

    def _raise_if_outside_bounds(self, line: int, column: int, msg: str) -> None:
        """Raise OutsideBounds exception if given coordinates are not inside the terminal."""
        if line < 0 or line >= self._process.lines:
            raise OutsideBounds(msg)

        if column < 0 or column >= self._process.columns:
            raise OutsideBounds(msg)

    def _get_attribute_at(self, line: int, column: int, attribute: str) -> object:
        """Get the provided pyte buffer attribute at the given coordinates."""
        self._update_screen()

        msg = (f"Coordinates ({line}, {column}) are invalid for terminal size"
               f" {self._process.lines}x{self._process.columns}")
        self._raise_if_outside_bounds(line, column, msg)

        return getattr(self._screen.buffer[line][column], attribute)

    def _dump(self):
        """Dump the contents of the terminal.

        Currently used for debugging purposes.
        """
        self._update_screen()
        print()
        print('-' * self._process.columns)
        print(*self._screen.display, sep='\n')
        print('-' * self._process.columns)
        print()
