"""Tests for various ways of specifying arguments of the executable under test."""


def test_arguments_can_be_specified_with_decorator(pytester, test_scripts_dir):
    """Verify that executable arguments can be specified with decorator."""
    pytester.makepyfile(
        f"""
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/run_command.sh")
        @tt.with_arguments(["echo", "x"])
        def test_arguments(terminal):
            terminal.wait_for_output()
            output = terminal.get_string_at(0, 0, 1)

            assert output == "x"
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_argument_sets_can_be_specified_through_parametrization(
        pytester, test_scripts_dir):
    """Verify that arguments can be specified through @pytest.mark.parametrize."""
    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/run_command.sh")
        @pytest.mark.parametrize("tuitest_arguments", indirect=True, argvalues=[
            ["echo", "1"],
            ["echo", "2"],
        ])
        def test_arguments(terminal):
            terminal.wait_for_output()
            output = terminal.get_string_at(0, 0, 1)

            assert output in ["1", "2"]
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)
