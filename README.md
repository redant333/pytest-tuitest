# What is this?

pytest_tuitest is a [pytest](https://pytest.org) plugin for testing TUI (text/terminal user interface) and regular command-line applications.

It allows you to run an application in a virtual terminal and run assertions on the contents and colors of its output.
It uses [pyte](https://github.com/selectel/pyte) for terminal emulation.

# What can it do?
Here are some examples to give you a taste of what can be done.

```python
import pytest_tuitest as tt

# You can simply run an application and verify that it prints
# the expected output in the terminal.

@tt.test_executable("grep")
@tt.with_arguments(["--color=always", "pytest_tuitest"])
@tt.with_stdin("This is a pytest_tuitest demo")
def test_grep_marks_the_output_according_to_arguments(terminal):
    terminal.wait_for_finished()

    # You can get the text in the terminal
    assert terminal.get_string_at(line=0, column=10, length=14) == "pytest_tuitest"

    # The color
    assert terminal.get_foreground_at(line=0, column=10) == tt.Color16.RED
    assert terminal.get_background_at(line=0, column=10) == tt.Color16.DEFAULT

    # Or the font style
    assert not terminal.has_style_at(line=0, column=10, style=tt.Style.BLINKING)

# You can also send stdin and capture stdout. Capturing stdout
# is useful in cases where TUI is printed on TTY and something
# else is printed on stdout (e.g. in case of fzf). That way, you
# can independently check what's in the TUI and what's "returned".

@tt.test_executable("fzf")
@tt.with_terminal_size(columns=80, lines=40)
@tt.with_stdin("things\nstuff")
@tt.with_captured_stdout(True)
def test_sending_input_and_capturing_output(terminal):
    terminal.wait_for_stable_output()

    assert terminal.get_string_at(line=39, column=0, length=1) == ">"

    # Emulate typing of "th" and pressing enter
    terminal.send("th\r\n")

    (status, stdout, _) = terminal.wait_for_finished()

    assert status == 0
    assert stdout == "things\n"
```

# Installation

```
pip install pytest-tuitest
```

This will automatically install pytest as well.
