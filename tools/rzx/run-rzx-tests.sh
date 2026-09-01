#!/usr/bin/env bash
set -e # Abort on errors

if [[ -z $SKOOLKIT_HOME ]]; then
  echo "ERROR: SKOOLKIT_HOME is not set"
  exit 1
fi
if [[ ! -d $SKOOLKIT_HOME ]]; then
  echo "ERROR: $SKOOLKIT_HOME: directory not found"
  exit 1
fi

if [[ -z $SPECTRUM_RZX_TESTS ]]; then
  echo "ERROR: SPECTRUM_RZX_TESTS is not set"
  exit 1
fi
if [[ ! -d $SPECTRUM_RZX_TESTS ]]; then
  echo "ERROR: $SPECTRUM_RZX_TESTS: directory not found"
  exit 1
fi

RZX_WORK=$SKOOLKIT_HOME/tools/rzx/rzx-work.txt
GEN_RZX_TESTS=$SKOOLKIT_HOME/tools/rzx/gen-rzx-tests.py

usage() {
  cat <<EOU
Usage: $(basename $0) [options]

  Run RZX file tests.

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
cd $SPECTRUM_RZX_TESTS
if [[ $CSIM -eq 1 ]]; then
  $GEN_RZX_TESTS -cj $PROCS $RZX_WORK
  RZX_TESTS="./test_rzxplay-c.py"
  RZX_TESTS_LOG=$SPECTRUM_RZX_TESTS/test_c.log
else
  NFRAMES=500
  $GEN_RZX_TESTS -j $PROCS $RZX_WORK $NFRAMES
  RZX_TESTS="pypy3 test_rzxplay-$NFRAMES.py"
  RZX_TESTS_LOG=$SPECTRUM_RZX_TESTS/test_p.log
fi

if ! $RZX_TESTS 2>&1 | tee $RZX_TESTS_LOG; then
  echo -e "\n\e[0;31mFAILED (see $RZX_TESTS_LOG)\e[0m"
fi
