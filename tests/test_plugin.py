"""Verify that fixtures and decorators function as expected."""
from pathlib import Path

TEST_SCRIPTS = str((Path("tests")/"test_scripts").absolute())


def test_executable_can_be_specified_with_decorator(pytester):
    """Verify that the executable can be specified with a decorator."""
    pytester.makepyfile(
        """
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts}/executable1.sh")
        def test_first_executable(terminal):
            terminal.wait_for_stable_output()
            executable_number = terminal.get_string_at(0, 0, 1)

            assert executable_number == "1"

        @tt.test_executable("{test_scripts}/executable2.sh")
        def test_second_executable(terminal):
            terminal.wait_for_stable_output()
            executable_number = terminal.get_string_at(0, 0, 1)

            assert executable_number == "2"
        """.format(test_scripts=TEST_SCRIPTS))

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_multiple_executables_can_be_specified_through_parametrization(pytester):
    """Verify that the executable can be specified through @pytest.mark.parametrize."""
    pytester.makepyfile(
        f"""
        import pytest

        @pytest.mark.parametrize("tuitest_executable", indirect=True, argvalues=[
            "{TEST_SCRIPTS}/executable1.sh",
            "{TEST_SCRIPTS}/executable2.sh",
        ])
        def test_parametrized_executable(terminal):
            terminal.wait_for_output()
            executable_number = terminal.get_string_at(0, 0, 1)

            assert executable_number in ["1", "2"]
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_not_specifying_executable_results_in_error(pytester):
    """Verify that not specifying the executable results in an error."""
    pytester.makepyfile(
        """
        def test_without_executable(terminal):
            pass
        """)

    result = pytester.runpytest()
    result.assert_outcomes(errors=1)

    msg = "Test raised the expected number of errors, but not the expected type"
    assert "TuitestSetupException" in result.stdout.str(), msg


def test_ini_executable_is_used_when_executable_not_provided(pytester):
    """Verify the default ini executable is used when the executable is not provided."""
    pytester.makeini(
        f"""
        [pytest]
        tuitest-default-executable = {TEST_SCRIPTS}/executable1.sh
        """)

    pytester.makepyfile(
        f"""
        import pytest_tuitest as tt

        def test_first_executable(terminal):
            terminal.wait_for_stable_output()
            executable_number = terminal.get_string_at(0, 0, 1)

            assert executable_number == "1"

        @tt.test_executable("{TEST_SCRIPTS}/executable2.sh")
        def test_second_executable(terminal):
            terminal.wait_for_stable_output()
            executable_number = terminal.get_string_at(0, 0, 1)

            assert executable_number == "2"
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_command_line_executable_is_used_when_executable_not_provided(pytester):
    """Verify the default CLI executable is used when the executable is not provided."""
    pytester.makepyfile(
        f"""
        import pytest_tuitest as tt

        def test_first_executable(terminal):
            terminal.wait_for_stable_output()
            executable_number = terminal.get_string_at(0, 0, 1)

            assert executable_number == "1"

        @tt.test_executable("{TEST_SCRIPTS}/executable2.sh")
        def test_second_executable(terminal):
            terminal.wait_for_stable_output()
            executable_number = terminal.get_string_at(0, 0, 1)

            assert executable_number == "2"
        """)

    result = pytester.runpytest(
        f"--tuitest-default-executable={TEST_SCRIPTS}/executable1.sh")
    result.assert_outcomes(passed=2)


def test_arguments_can_be_specified_with_decorator(pytester):
    """Verify that executable arguments can be specified with decorator."""
    pytester.makepyfile(
        f"""
        import pytest_tuitest as tt

        @tt.test_executable("{TEST_SCRIPTS}/run_command.sh")
        @tt.with_arguments(["echo", "x"])
        def test_arguments(terminal):
            terminal.wait_for_output()
            output = terminal.get_string_at(0, 0, 1)

            assert output == "x"
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_argument_sets_can_be_specified_through_parametrization(pytester):
    """Verify that arguments can be specified through @pytest.mark.parametrize."""
    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{TEST_SCRIPTS}/run_command.sh")
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
