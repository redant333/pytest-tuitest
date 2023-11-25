"""Tasks for task runner doit."""
DOIT_CONFIG = {"action_string_formatting": "both"}


def task_check():
    """Run all pre-commit checks."""
    return {
        "verbosity": 2,
        "actions": [
            "pre-commit run --all-files --color=always"
        ]
    }


def task_test():
    """Run tests.

    Additional pytest args can be added after --. For example:
    $ doit test -- -k some_test
    """
    return {
        "verbosity": 2,
        "actions": [
            "pytest --color=yes tests {additional_args}"
        ],
        "pos_arg": "additional_args",
    }
