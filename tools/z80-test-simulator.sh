#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

mkdir -p "$SPECTRUM_SIM_TESTS"

TEST_SIMULATOR="$TOOLS/z80-test-simulator.py"

make -C $SKOOLKIT_HOME cmods

DOC_TESTS_TAP="${SPECTRUM_SIM_TESTS}/z80doc.tap"
if [[ ! -f $DOC_TESTS_TAP ]]; then
  DOC_TESTS_ZIP="${SPECTRUM_SIM_TESTS}/z80test.zip"
  wget -O "$DOC_TESTS_ZIP" https://github.com/raxoft/z80test/releases/download/v1.2a/z80test-1.2a.zip
  unzip -j "$DOC_TESTS_ZIP" z80test-1.2a/z80doc.tap -d "$SPECTRUM_SIM_TESTS"
  rm "$DOC_TESTS_ZIP"
fi

csimlog="$SPECTRUM_SIM_TESTS/z80-test-simulator-csim.log"
ccmiolog="$SPECTRUM_SIM_TESTS/z80-test-simulator-ccmio.log"
simlog="$SPECTRUM_SIM_TESTS/z80-test-simulator-sim.log"
cmiolog="$SPECTRUM_SIM_TESTS/z80-test-simulator-cmio.log"

$TEST_SIMULATOR --csim $DOC_TESTS_TAP &> $csimlog & PIDcsim=$!
$TEST_SIMULATOR --ccmio $DOC_TESTS_TAP &> $ccmiolog & PIDccmio=$!
$TEST_SIMULATOR --sim $DOC_TESTS_TAP &> $simlog & PIDsim=$!
$TEST_SIMULATOR --cmio $DOC_TESTS_TAP &> $cmiolog & PIDcmio=$!

echo
wait_log "CSimulator tests" $PIDcsim "(see $csimlog)"
wait_log "CCMIOSimulator tests" $PIDccmio "(see $ccmiolog)"
wait_log "Simulator tests" $PIDsim "(see $simlog)"
wait_log "CMIOSimulator tests" $PIDcmio "(see $cmiolog)"
