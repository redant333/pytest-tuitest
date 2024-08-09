"""Text styles."""

from enum import Enum, auto


class Style(Enum):
    """Style of text in terminal."""
    BOLD = auto()
    ITALIC = auto()
    UNDERLINE = auto()
    BLINKING = auto()
    INVERSE = auto()
    STRIKETHROUGH = auto()
