#!/usr/bin/env bash
set -e # Abort on errors

for v in SKOOLKIT_HOME SPECTRUM_PZX_TESTS; do
  VDIR=${!v}
  if [[ -z $VDIR ]]; then
    echo "ERROR: $v is not set"
    exit 1
  fi
  if [[ ! -d $VDIR ]]; then
    echo "ERROR: $VDIR: directory not found"
    exit 1
  fi
done

PZX_TOOLS=$SKOOLKIT_HOME/tools/pzx

usage() {
  cat <<EOU
Usage: $(basename $0) [options]

  Run PZX file tests.

Options:
  -c        Run tests using CSimulator instead of Simulator.
  -j PROCS  Run tests using this many processes.
EOU
  exit 1
}

CSIM=0
PROCS=1
while getopts ":cj:" opt; do
  case $opt in
    c) CSIM=1 ;;
    j) PROCS=$OPTARG ;;
    *) usage ;;
  esac
done

make -C $SKOOLKIT_HOME cmods
cd $SPECTRUM_PZX_TESTS

echo -en "\nRemoving unused and outdated PZX files..."
$PZX_TOOLS/remove-unused-and-outdated-pzx.sh &> /dev/null
echo "done"

echo -e "\nGenerating new PZX files"
if ! $PZX_TOOLS/gen-pzx-files.sh; then
  echo -e "\n\e[0;31mFailed to generate PZX files\e[0m"
  exit 1
fi

if [[ $CSIM -eq 1 ]]; then
  GPT_OPTS="-c"
  PZX_TESTS="./test_pzx_c.py"
  PZX_TESTS_LOG=$SPECTRUM_PZX_TESTS/test_c.log
else
  PZX_TESTS="pypy3 test_pzx.py"
  PZX_TESTS_LOG=$SPECTRUM_PZX_TESTS/test_p.log
fi

$PZX_TOOLS/gen-pzx-test.py $GPT_OPTS -j $PROCS pzx

if ! $PZX_TESTS 2>&1 | tee $PZX_TESTS_LOG; then
  echo -e "\n\e[0;31mFAILED (see $PZX_TESTS_LOG)\e[0m"
fi
