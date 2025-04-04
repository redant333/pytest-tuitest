"""
.. include:: ../../README.md
"""

__version__ = "0.1.0"

from .colors import Color16, Color256
from .plugin import (test_executable, with_arguments, with_captured_stderr,
                     with_captured_stdout, with_env, with_stdin,
                     with_terminal_size)
from .process import Process, ProcessFinished
from .styles import Style
from .terminal import OutsideBounds, Terminal, TimedOut
