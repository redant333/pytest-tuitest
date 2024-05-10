# Check whether the task is running inside a Python virtual environment.
# This is used for tasks that with inside-venv dependencies.
# See https://docs.python.org/3/library/venv.html#how-venvs-work for details
# on the detection method.
_in-venv:
    #!/usr/bin/env python3
    import sys

    if sys.prefix == sys.base_prefix:
        print("You need to have the virtual environment initialized and activated to run this")
        exit(1)
    else:
        exit(0)

# Run all pre-commit checks
pre-commit: _in-venv
    pre-commit run --all-files --color=always

# Run pytest on the tests folder. If provided, additional_args will be forwarded to pytest
test *additional_args: _in-venv
    pytest --color=yes tests {{additional_args}}

# Initialize the development virutial environment in ./env
init-venv:
    #!/bin/bash -eu
    if [ -d env ]; then
        echo "Directory env already exists"
        exit 1
    fi

    python3 -m venv env
    source env/bin/activate
    pip install --editable '.[dev]'

    echo ""
    echo "Environment initialized. Activate it with:"
    echo "  source env/bin/activate"
