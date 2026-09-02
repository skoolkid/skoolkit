#!/usr/bin/env bash
set -e # Abort on errors

for v in SKOOLKIT_HOME T2SFILES_HOME SPECTRUM_T2SFILES_TESTS; do
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

GEN_T2SFILES_TEST=$T2SFILES_HOME/tools/gen-t2sfiles-test.py

usage() {
  cat <<EOU
Usage: $(basename $0) [options]

  Run t2s file tests.

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
cd $SPECTRUM_T2SFILES_TESTS
if [[ $CSIM -eq 1 ]]; then
  GTT_OPTS="-c"
  T2SFILES_TESTS="./test_t2sfiles_c.py"
  T2SFILES_TESTS_LOG=$SPECTRUM_T2SFILES_TESTS/test_c.log
else
  T2SFILES_TESTS="pypy3 test_t2sfiles.py"
  T2SFILES_TESTS_LOG=$SPECTRUM_T2SFILES_TESTS/test_p.log
fi

$GEN_T2SFILES_TEST $GTT_OPTS -j $PROCS $T2SFILES_HOME/t2s '' none

if ! $T2SFILES_TESTS 2>&1 | tee $T2SFILES_TESTS_LOG; then
  echo -e "\n\e[0;31mFAILED (see $T2SFILES_TESTS_LOG)\e[0m"
fi
