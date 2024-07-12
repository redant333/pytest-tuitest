"""Tests for specifying terminal size through fixtures and decorators."""


def test_size_can_be_specified_with_decorator(pytester):
    """Verify that terminal size can be specified through with_terminal_size."""
    pytester.makepyfile(
        """
        import pytest_tuitest as tt

        @tt.test_executable("python3")
        @tt.with_arguments(["-c", ("from os import get_terminal_size;"
                                   "print(get_terminal_size().columns,"
                                   "get_terminal_size().lines)")
                            ])
        @tt.with_terminal_size(21, 22)
        def test_terminal_size(terminal):
            terminal.wait_for_output()
            output = terminal.get_string_at(0, 0, 5)

            assert output == "21 22"
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_sizes_can_be_specified_with_through_parametrization(pytester):
    """Verify that multiple sizes can be set by using @pytest.mark.parametrize."""
    pytester.makepyfile(
        """
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("python3")
        @tt.with_arguments(["-c", ("from os import get_terminal_size;"
                                   "print(get_terminal_size().columns,"
                                   "get_terminal_size().lines)")
                            ])
        @pytest.mark.parametrize("tuitest_terminal_size", indirect=True, argvalues=[
            (21, 22),
            (23, 24),
        ])
        def test_terminal_size(terminal):
            terminal.wait_for_output()
            output = terminal.get_string_at(0, 0, 5)

            assert (output == "21 22" or output == "23 24")
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)
