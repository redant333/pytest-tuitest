"""Tests for specifying environment variables for process under test."""


def test_environment_can_be_specified_with_decorator(pytester):
    """Verify that the environment can be specified with the decorator."""
    pytester.makepyfile(
        """
        import pytest_tuitest as tt

        @tt.test_executable("bash")
        @tt.with_arguments(["-c", "echo $SOME_VAR"])
        @tt.with_env({"SOME_VAR": "stuff"})
        def test_terminal_size(terminal):
            terminal.wait_for_output()
            output = terminal.get_string_at(0, 0, 5)

            assert output == "stuff"
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_environments_can_be_specified_with_through_parametrization(pytester):
    """Verify that multiple environments can be set by using @pytest.mark.parametrize."""
    pytester.makepyfile(
        """
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("bash")
        @tt.with_arguments(["-c", "echo $SOME_VAR"])
        @pytest.mark.parametrize("tuitest_env", indirect=True, argvalues=[
            {"SOME_VAR": "thing"},
            {"SOME_VAR": "stuff"},
        ])
        def test_terminal_size(terminal):
            terminal.wait_for_output()
            output = terminal.get_string_at(0, 0, 5)

            assert (output == "thing" or output == "stuff")
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)
