"""Module for virtual terminal interaction."""
import string
import time

import pyte

from pytest_tuitest.styles import Style

from .colors import Color16
from .process import Process, ProcessFinished

_PYTE_TO_COLOR_NAMED_MAP = {
    "black": Color16.BLACK,
    "red": Color16.RED,
    "green": Color16.GREEN,
    "brown": Color16.YELLOW,
    "blue": Color16.BLUE,
    "magenta": Color16.MAGENTA,
    "cyan": Color16.CYAN,
    "white": Color16.WHITE,
    "brightblack": Color16.BRIGHT_BLACK,
    "brightred": Color16.BRIGHT_RED,
    "brightgreen": Color16.BRIGHT_GREEN,
    "brightbrown": Color16.BRIGHT_YELLOW,
    "brightblue": Color16.BRIGHT_BLUE,
    "brightmagenta": Color16.BRIGHT_MAGENTA,
    # pyte typo for background colors
    "bfightmagenta": Color16.BRIGHT_MAGENTA,
    "brightcyan": Color16.BRIGHT_CYAN,
    "brightwhite": Color16.BRIGHT_WHITE,
    "default": Color16.DEFAULT,
}

_STYLE_PYTE_ATTRIBUTE_MAP = {
    Style.BOLD: "bold",
    Style.ITALIC: "italics",
    Style.UNDERLINE: "underscore",
    Style.BLINKING: "blink",
    Style.INVERSE: "reverse",
    Style.STRIKETHROUGH: "strikethrough",
}


def _is_rgb_string(string_to_check: str):
    """Check whether the given string is a 6-digit RBG string."""
    all_hex_digits = all(
        c in string.hexdigits for c in string_to_check)
    good_len = len(string_to_check) == 6

    return good_len and all_hex_digits


class Terminal:
    """A class for terminal emulation and interaction."""

    def __init__(self, process: Process) -> None:
        """Initialize a Terminal object.

        Args:
            process: The process to execute in this virtual terminal.
        """
        self._screen = pyte.Screen(process.columns, process.lines)
        self._stream = pyte.ByteStream(self._screen)
        self._process = process
        self._process_running = True

    def get_string_at(self, line: int, column: int, length: int) -> str:
        """Get the string of given length at the given coordiantes in the terminal.

        This method only supports getting a string that is completely located on
        one line. For locations without any text, this method uses a space character.

        Args:
            line: Line where the string starts (zero indexed).
            column: Column where the string starts (zero indexed).
            length: Length of the string.

        Raises:
            `OutsideBounds`: If the string is not completely located within the
                terminal bounds.

        Returns:
            The requested string.
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

    def get_foreground_at(self, line: int, column: int) -> (Color16 | str):
        """Get the foreground color at given coordinates.

        Args:
            line: The line at which to get the color.
            column: The column at which to get the color.

        Returns:
                Color at the given coordinates as a named color
                or a 6 digit hex string. Note that, due to limitations of the
                underlying library, RGB colors cannot be distingquished from
                ANSI 256 colors and both are returned as RBG strings. Use
                `pytest_tuitest.colors.Color256` enum to compare the returned
                string with ANSI 256 index.
        """
        pyte_color = self._get_attribute_at(line, column, "fg")

        if pyte_color in _PYTE_TO_COLOR_NAMED_MAP:
            return _PYTE_TO_COLOR_NAMED_MAP[pyte_color]
        elif _is_rgb_string(pyte_color):
            return pyte_color

        msg = f"Unrecognized color at line {line}, column {column}"
        raise UnrecognizedColor(msg)

    def get_background_at(self, line: int, column: int) -> (Color16 | str):
        """Get the background color at given coordinates.

        Args:
            line: The line at which to get the color.
            column: The column at which to get the color.

        Returns:
                Color at the given coordinates as a named color
                or a 6 digit hex string. Note that, due to limitations of the
                underlying library, RGB colors cannot be distingquished from ANSI 256
                colors and both are returned as RBG strings. Use `pytest_tuitest.colors.Color256`
                enum to compare the returned string with ANSI 256 index.
        """
        pyte_color = self._get_attribute_at(line, column, "bg")

        if pyte_color in _PYTE_TO_COLOR_NAMED_MAP:
            return _PYTE_TO_COLOR_NAMED_MAP[pyte_color]
        elif _is_rgb_string(pyte_color):
            return pyte_color

        msg = f"Unrecognized color at line {line}, column {column}"
        raise UnrecognizedColor(msg)

    def has_style_at(self, style: Style, line: int, column: int) -> bool:
        """Check whether the given location is styled with the given style

        Args:
            style: The style to check
            line: The line at which to check the style
            column: The column at which to check the style

        Returns:
            True if the location has the given stylem, False otherwise.
        """
        attr = _STYLE_PYTE_ATTRIBUTE_MAP[style]
        return self._get_attribute_at(line, column, attr)

    def wait_for_output(self) -> None:
        """Block until new output is received from the process."""
        self._process.wait_for_output()

    def wait_for_finished(self, encoding: str = "utf8") -> tuple[int, str, str]:
        """Block until the process finishes and return the information about it.

        Args:
            encoding: The encoding to be used to decode captured outputs.

        Returns:
            A tuple with the following information about the process:

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
            stable_time_sec: The terminal is considered stable
                after it remains unchanged for this amount of time. Defaults to 0.1.
            max_wait_sec: Maximum amount of time to wait for the
                terminal to become stable. Defaults to 5.

        Raises:
            `TimedOut`: When the terminal doesn't stabilize within max_wait_sec.
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
            characters: The characters to send.
        """
        encoded = characters.encode()
        self._process.write(encoded)

    def _update_screen(self) -> bool:
        """Refresh the internal knowledge about the process output.

        Returns:
            True if the screen has changed, False otherwise.
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


class OutsideBounds(Exception):
    """Raised when information is requested for invalid coordinates."""


class TimedOut(Exception):
    """Raised when an operation times out."""


class UnrecognizedColor(Exception):
    """Raised when a color cannot be decoded."""
