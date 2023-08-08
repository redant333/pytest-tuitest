"""Tasks for task runner doit."""


def task_check():
    """Run all pre-commit checks."""
    return {
        "verbosity": 2,
        "actions": [
            "pre-commit run --all-files"
        ]
    }


def task_test():
    """Run tests."""
    return {
        "verbosity": 2,
        "actions": [
            "pytest --color=yes tests"
        ]
    }
