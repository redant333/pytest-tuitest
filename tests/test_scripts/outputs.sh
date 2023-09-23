#!/bin/bash
echo This goes to stdout
echo This goes to stderr >&2
echo This goes to /dev/tty > /dev/tty
