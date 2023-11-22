"""Verify that fixtures and decorators function as expected."""


def test_terminal_fixture_exists(pytester):
    """Verify that terminal fixture is accessible."""
    pytester.makepyfile(
        """
        def test_terminal_fixture(terminal):
            pass
        """)

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
