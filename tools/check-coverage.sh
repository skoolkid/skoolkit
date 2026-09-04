#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

require_dir SKOOLKIT_HOME

COVERAGE=python3-coverage
ERR_ON="\e[0;31m"
ERR_OFF="\e[0m"
failed=0

cd $SKOOLKIT_HOME

make remove-disassembly-tests remove-c
$COVERAGE run --rcfile .coveragerc-python -m nose2 -s tests
$COVERAGE report --rcfile .coveragerc-python --fail-under 100 -m || ((failed += 1))

make cmods
$COVERAGE run --rcfile .coveragerc-c -m nose2 -s tests
$COVERAGE report --rcfile .coveragerc-c --fail-under 100 -m || ((failed += 2))

if ((failed & 1)); then
  echo -e "${ERR_ON}FAILED: Python coverage is less than 100%${ERR_OFF}"
fi
if ((failed & 2)); then
  echo -e "${ERR_ON}FAILED: C coverage is less than 100%${ERR_OFF}"
fi

exit $failed
