"""Verify that fixtures and decorators function as expected."""
from pathlib import Path

TEST_SCRIPTS = str((Path("tests")/"test_scripts").absolute())


def test_terminal_fixture_exists(pytester):
    """Verify that terminal fixture is accessible."""
    pytester.makepyfile(
        """
        def test_terminal_fixture(terminal):
            pass
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


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
