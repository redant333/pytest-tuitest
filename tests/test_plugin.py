"""Verify that fixtures and decorators function as expected."""

def test_terminal_fixture_has_correct_type(terminal):
    """Verify that terminal fixture is accessible and has the correct type."""
    class_name = type(terminal).__name__

    assert class_name == "Terminal", "Fixture terminal has incorrect type"
