#!/bin/bash

DO_FORMAT=0
if [ "$1" == "format" ]; then
    DO_FORMAT=1
fi

echo "Black on py38:"
if [ "$DO_FORMAT" == "0" ]; then
    python -m black . --diff --color --check -t py38
else
    python -m black . -t py38
fi
echo "----"
echo ""

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
pylint --recursive=y .
echo "----"
echo ""



#echo "Checking for i18n data missing from source base..."
#python ./tests/test_missing_i18n.py
#echo "----"

#echo "Bandit:"
#bandit -r .
#echo "----"



