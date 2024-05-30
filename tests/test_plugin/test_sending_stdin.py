"""Tests for specifying stdin."""


def test_stdin_can_be_specified_through_decorator(pytester):
    """Verify that stdin can be specified using the decorator."""
    pytester.makepyfile(
        """
        import pytest_tuitest as tt

        @tt.test_executable("wc")
        @tt.with_arguments(["-c"])
        @tt.with_stdin("test")
        def test_stdout_capture(terminal):
            terminal.wait_for_stable_output()

            output = terminal.get_string_at(0, 0, 1)

            assert output == "4"
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_stdin_not_sent_when_not_specified(pytester):
    """Verify that the stdin is not sent when not requested."""
    pytester.makepyfile(
        """
        import pytest_tuitest as tt

        @tt.test_executable("wc")
        @tt.with_arguments(["-c"])
        def test_stdout_capture(terminal):
            terminal.wait_for_stable_output()

            output = terminal.get_string_at(0, 0, 1)

            # wc should hang with no output
            assert output == " "
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_empty_stdin_can_be_sent(pytester):
    """Verify that the stdin is not sent when not requested."""
    pytester.makepyfile(
        """
        import pytest_tuitest as tt

        @tt.test_executable("wc")
        @tt.with_arguments(["-c"])
        @tt.with_stdin("")
        def test_stdout_capture(terminal):
            terminal.wait_for_stable_output()

            output = terminal.get_string_at(0, 0, 1)

            assert output == "0"
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_stdins_can_be_specified_through_parametrization(pytester):
    """Verify that stdin can be specified through @pytest.mark.parametrize."""
    pytester.makepyfile(
        """
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("wc")
        @tt.with_arguments(["-c"])
        @pytest.mark.parametrize("tuitest_stdin, expected", [
            ("this", "4"),
            ("is", "2"),
            ("a", "1"),
            ("test", "4")],
            indirect=["tuitest_stdin"])
        def test_stdout_capture(terminal, expected):
            terminal.wait_for_stable_output()

            output = terminal.get_string_at(0, 0, 1)

            assert output == expected
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=4)
