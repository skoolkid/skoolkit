#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

mkdir -p "$SPECTRUM_SIM_TESTS"

FLAGS_TEST="$TOOLS/z80-flags-test.py"

make -C $SKOOLKIT_HOME cmods

FLAGS_TEST_TAP="${SPECTRUM_SIM_TESTS}/z80-flags.tap"
if [[ ! -f $FLAGS_TEST_TAP ]]; then
  # Or https://zxe.io/depot/software/ZX%20Spectrum/Z80%20Test%20Suite%20%282008%29%28Woodmass,%20Mark%29%5B%21%5D.tap
  wget -O "$FLAGS_TEST_TAP" https://skoolkit.ca/tapes/z80-flags.tap
fi

csimlog="$SPECTRUM_SIM_TESTS/z80-flags-test-csim.log"
ccmiolog="$SPECTRUM_SIM_TESTS/z80-flags-test-ccmio.log"
simlog="$SPECTRUM_SIM_TESTS/z80-flags-test-sim.log"
cmiolog="$SPECTRUM_SIM_TESTS/z80-flags-test-cmio.log"

$FLAGS_TEST --csim $FLAGS_TEST_TAP &> $csimlog & PIDcsim=$!
$FLAGS_TEST --ccmio $FLAGS_TEST_TAP &> $ccmiolog & PIDccmio=$!
$FLAGS_TEST --sim $FLAGS_TEST_TAP &> $simlog & PIDsim=$!
$FLAGS_TEST --cmio $FLAGS_TEST_TAP &> $cmiolog & PIDcmio=$!

echo
wait_log "CSimulator tests" $PIDcsim "(see $csimlog)"
wait_log "CCMIOSimulator tests" $PIDccmio "(see $ccmiolog)"
wait_log "Simulator tests" $PIDsim "(see $simlog)"
wait_log "CMIOSimulator tests" $PIDcmio "(see $cmiolog)"
