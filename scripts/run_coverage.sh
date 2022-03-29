#!/bin/bash
set -e

BLUE="\033[0;38;5;12m"
RESET="\033[0m"
if [[ -z "$CI" ]]; then
    REPORT_TYPE="html"
else
    REPORT_TYPE="xml"
fi

echo -e "${BLUE}Running tests and generating ${REPORT_TYPE} coverage report${RESET}"
poetry install
poetry run pytest --cov=sql_to_pypika --cov-report=$REPORT_TYPE tests
