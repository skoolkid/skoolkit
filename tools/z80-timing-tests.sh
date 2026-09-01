#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

mkdir -p "$SPECTRUM_SIM_TESTS"

TIMING_TESTS="$TOOLS/z80-timing-tests.py"

make -C $SKOOLKIT_HOME cmods

TIMING_TESTS_TAP="${SPECTRUM_SIM_TESTS}/z80-timing.tap"
if [[ ! -f $TIMING_TESTS_TAP ]]; then
  # Or https://zxe.io/depot/software/ZX%20Spectrum/ZX%20Spectrum%20Timing%20Tests%20-%2048K%20v1.0%20%282010-04-14%29%28Butler%2C%20Richard%3B%20Butler%2C%20Tim%29%5B%21%5D.tap
  wget -O "$TIMING_TESTS_TAP" https://skoolkit.ca/tapes/z80-timing.tap
fi

ccmiolog="$SPECTRUM_SIM_TESTS/z80-timing-tests-ccmio.log"
cmiolog="$SPECTRUM_SIM_TESTS/z80-timing-tests-cmio.log"

$TIMING_TESTS --ccmio $TIMING_TESTS_TAP &> $ccmiolog & PIDccmio=$!
$TIMING_TESTS --cmio $TIMING_TESTS_TAP &> $cmiolog & PIDcmio=$!

echo
wait_log "CCMIOSimulator tests" $PIDccmio "(see $ccmiolog)"
wait_log "CMIOSimulator tests" $PIDcmio "(see $cmiolog)"
