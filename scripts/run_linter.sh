#!/bin/bash
set -e

BLUE="\033[0;38;5;12m"
RESET="\033[0m"
if [[ -z "$CI" ]]; then
    echo -e "${BLUE}Running 'Black' in auto-reformatting mode${RESET}"
    EXTRA_ARGS=""
else
    echo -e "${BLUE}Running 'Black' validation${RESET}"
    EXTRA_ARGS="--check"
fi

poetry install
poetry run black . --line-length 120 $EXTRA_ARGS
