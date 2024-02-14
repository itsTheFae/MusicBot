#!/bin/bash

HELP_ME=0
DO_FORMAT=0
DO_SPELLING=0
DO_OPTIONAL=0
ONLY_BASE_CHECKS=0
while [[ $# -gt 0 ]] ; do
case $1 in
    "format"|"--format")
        DO_FORMAT=1
        shift
    ;;
    "spell"|"spelling"|"--spelling")
        DO_SPELLING=1
        shift
    ;;
    "base")
        # only check with black
        ONLY_BASE_CHECKS=1
        shift
    ;;
    "opt"|"optional")
        DO_OPTIONAL=1
        shift
    ;;
    "help"|"--help"|"-h")
        HELP_ME=1
        shift
    ;;
    *)
        shift
    ;;
esac
done


if [ "$HELP_ME" == "1" ]; then
    echo "$0"
    echo "Code checks helper script."
    echo ""
    echo "Available Options:"
    echo " -h or help   Show this message and exit"
    echo " format       Run code format via isort and black automatically."
    echo " spell        Run spelling check, if pylint is configured for it."
    echo " base         Only run basic black check. Option format will still apply if set."
    echo " optional     Adds extra checks. Currently only bandit."
    echo ""

    exit 0
fi


echo "Black on py38:"
if [ "$DO_FORMAT" == "0" ]; then
    python -m black . --diff --color --check -t py38
else
    python -m black . -t py38
fi
echo "----"
echo ""

if [ "$ONLY_BASE_CHECKS" == "1" ] ; then
  echo "Skipping all other checks."
  exit 0
fi

echo "isort imports:"
if [ "$DO_FORMAT" == "0" ]; then
    isort . --check --diff --color --profile black
else
    isort . --profile black
fi
echo "----"
echo ""

echo "Flake8:"
python -m flake8
echo "----"
echo ""

echo "MyPy:"
mypy --python-version 3.8 --warn-unused-ignores ./*.py
echo "----"
echo ""

echo "pylint:"
if [ "$DO_SPELLING" == "1" ]; then
    pylint --recursive=y --spelling-dict=en_US --spelling-private-dict-file=./tests/repo-dictionary.txt .
else
    pylint --recursive=y .
fi
echo "----"
echo ""


if [ "$DO_OPTIONAL" == "1" ]; then

echo "Bandit:"
bandit -r .
echo "----"

#echo "Checking for i18n data missing from source base..."
#python ./tests/test_missing_i18n.py
#echo "----"

fi

