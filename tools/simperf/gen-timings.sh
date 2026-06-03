#!/usr/bin/env bash
usage() {
  cat <<EOU
Usage: $(basename $0) [options]

  Generate (C)(CMIO)Simulator timings files.

Options:
  -s DIR  Use SkoolKit in this directory (instead of the current development
          version in \$SKOOLKIT_HOME).
EOU
  exit 1
}

SK_HOME=$SKOOLKIT_HOME
while getopts ":s:" opt; do
  case $opt in
    s) SK_HOME=$OPTARG ;;
    *) usage ;;
  esac
done

for copt in "" "-c"; do
  ./run-timer.py rzxplay -s $SK_HOME $copt
  ./run-timer.py simulator -s $SK_HOME $copt --cmio
  ./run-timer.py simulator -s $SK_HOME $copt -i
  ./run-timer.py simulator -s $SK_HOME $copt
  ./run-timer.py tap2sna -s $SK_HOME $copt
  ./run-timer.py trace -s $SK_HOME $copt --cmio
  ./run-timer.py trace -s $SK_HOME $copt
done
