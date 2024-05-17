"""Tests for capturing stderr in tests."""


def test_stderr_not_captured_by_default(pytester, test_scripts_dir):
    """Verify that stderr is sent to the virtual terminal by default."""
    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/echo_to_stderr.sh")
        @tt.with_arguments(["X"])
        def test_stderr_capture(terminal):
            (status, _, stderr) = terminal.wait_for_finished()

            assert status == 0, "Process unexpectedly failed"
            assert stderr == None, "Expected no stderr, something detected"

            msg = "Screen not as expected"
            assert terminal.get_string_at(0, 0, 1) == "X", msg
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_stderr_captured_if_with_captured_stderr_is_used(pytester, test_scripts_dir):
    """Verify that stderr can be captured with a decorator."""
    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/echo_to_stderr.sh")
        @tt.with_arguments(["X"])
        @tt.with_captured_stderr()
        def test_stderr_capture(terminal):
            (status, _, stderr) = terminal.wait_for_finished()

            assert status == 0, "Process unexpectedly failed"
            assert stderr == "X", "Captured stderr not as expected"

            msg = "Expected empty screen, found something at 0,0"
            assert terminal.get_string_at(0, 0, 1) != "X", msg
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_stderr_captured_if_ini_option_set_to_true(pytester, test_scripts_dir):
    """Verify that specifying stderr capture in the ini file causes stderr to be captured."""
    pytester.makeini(
        """
        [pytest]
        tuitest-capture-stderr = true
        """)

    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/echo_to_stderr.sh")
        @tt.with_arguments(["X"])
        def test_stderr_capture(terminal):
            (status, _, stderr) = terminal.wait_for_finished()

            assert status == 0, "Process unexpectedly failed"
            assert stderr == "X", "Captured stderr not as expected"

            msg = "Expected empty screen, found something at 0,0"
            assert terminal.get_string_at(0, 0, 1) != "X", msg
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_decorator_has_higher_priority_than_ini_option(pytester, test_scripts_dir):
    """Verify that the stderr capture value from ini file has higher priority than the decorator."""
    pytester.makeini(
        """
        [pytest]
        tuitest-capture-stderr = true
        """)

    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/echo_to_stderr.sh")
        @tt.with_arguments(["X"])
        @tt.with_captured_stderr(False)
        def test_stderr_capture(terminal):
            (status, _, stderr) = terminal.wait_for_finished()

            assert status == 0, "Process unexpectedly failed"
            assert stderr == None, "Captured stderr not expected but received"

            msg = "Found unexpected value on the screen"
            assert terminal.get_string_at(0, 0, 1) != " ", msg
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_stderr_can_be_captured_even_when_empty(pytester, test_scripts_dir):
    """Verify that stderr can be even when there is nothing on it."""
    pytester.makepyfile(
        f"""
        import pytest
        import pytest_tuitest as tt

        @tt.test_executable("{test_scripts_dir}/run_command.sh")
        @tt.with_arguments(["true"])
        @tt.with_captured_stderr()
        def test_stdout_capture(terminal):
            (status, _, stderr) = terminal.wait_for_finished()

            assert status == 0, "Process unexpectedly failed"
            assert stderr == "", "Captured stderr not as expected"
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
