#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

mkdir -p "$SPECTRUM_SIM_TESTS"

MEMPTR_TESTS="$TOOLS/z80-memptr-tests.py"

make -C $SKOOLKIT_HOME cmods

MEMPTR_TESTS_TZX="${SPECTRUM_SIM_TESTS}/cpd-test1250429.tzx"
if [[ ! -f $MEMPTR_TESTS_TZX ]]; then
  # Or https://zxe.io/depot/software/ZX%20Spectrum/CPD-Test%20v0.7b%20%282025-04-29%29%28Sapach%2C%20Michael%29%28TAP%29%5B%21%5D.zip
  wget -O "$MEMPTR_TESTS_TZX" https://skoolkit.ca/tapes/cpd-test1250429.tzx
fi

ccmio48log="$SPECTRUM_SIM_TESTS/z80-memptr-tests-ccmio-48.log"
ccmio128log="$SPECTRUM_SIM_TESTS/z80-memptr-tests-ccmio-128.log"
cmio48log="$SPECTRUM_SIM_TESTS/z80-memptr-tests-cmio-48.log"
cmio128log="$SPECTRUM_SIM_TESTS/z80-memptr-tests-cmio-128.log"

$MEMPTR_TESTS --ccmio $MEMPTR_TESTS_TZX &> $ccmio48log & PIDccmio48=$!
$MEMPTR_TESTS --ccmio --128 $MEMPTR_TESTS_TZX &> $ccmio128log & PIDccmio128=$!
$MEMPTR_TESTS --cmio $MEMPTR_TESTS_TZX &> $cmio48log & PIDcmio48=$!
$MEMPTR_TESTS --cmio --128 $MEMPTR_TESTS_TZX &> $cmio128log & PIDcmio128=$!

echo
wait_log "CCMIOSimulator 48K tests" $PIDccmio48 "(see $ccmio48log)"
wait_log "CCMIOSimulator 128K tests" $PIDccmio128 "(see $ccmio128log)"
wait_log "CMIOSimulator 48K tests" $PIDcmio48 "(see $cmio48log)"
wait_log "CMIOSimulator 128K tests" $PIDcmio128 "(see $cmio128log)"
