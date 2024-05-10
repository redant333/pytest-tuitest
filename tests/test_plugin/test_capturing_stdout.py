"""Tests for capturing stdout in tests."""


def test_stdout_not_captured_by_default(pytester, test_scripts_dir):
    """Verify that stdout is sent to the virtual terminal by default."""
    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/run_command.sh")
        @tt.with_arguments(["echo", "-n", "X"])
        def test_arguments(terminal):
            (status, stdout, _) = terminal.wait_for_finished()

            assert status == 0, "Process unexpectedly failed"
            assert stdout == None, "Expected no stdout, something detected"

            msg = "Screen not as expected"
            assert terminal.get_string_at(0, 0, 1) == "X", msg
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_stdout_captured_if_with_captured_stdout_is_used(pytester, test_scripts_dir):
    """Verify that stdout can be captured with a decorator."""
    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/run_command.sh")
        @tt.with_arguments(["echo", "-n", "X"])
        @tt.with_captured_stdout()
        def test_arguments(terminal):
            (status, stdout, _) = terminal.wait_for_finished()

            assert status == 0, "Process unexpectedly failed"
            assert stdout == b"X", "Captured stdout not as expected"

            msg = "Expected empty screen, found something at 0,0"
            assert terminal.get_string_at(0, 0, 1) != "X", msg
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
