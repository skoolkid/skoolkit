#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

mkdir -p "$SPECTRUM_SIM_TESTS"

JSON_TEST_SIMULATOR="$TOOLS/json-test-simulator.py"

make -C $SKOOLKIT_HOME cmods

JSON_TESTS_DIR="${SPECTRUM_SIM_TESTS}/json-tests"
if [[ ! -d $JSON_TESTS_DIR ]]; then
  git clone https://github.com/SingleStepTests/z80.git $JSON_TESTS_DIR
fi

csimlog="$SPECTRUM_SIM_TESTS/json-test-simulator-csim.log"
ccmiolog="$SPECTRUM_SIM_TESTS/json-test-simulator-ccmio.log"
simlog="$SPECTRUM_SIM_TESTS/json-test-simulator-sim.log"
cmiolog="$SPECTRUM_SIM_TESTS/json-test-simulator-cmio.log"

$JSON_TEST_SIMULATOR --csim $JSON_TESTS_DIR/v1/* &> $csimlog & PIDcsim=$!
$JSON_TEST_SIMULATOR --ccmio $JSON_TESTS_DIR/v1/* &> $ccmiolog & PIDccmio=$!
$JSON_TEST_SIMULATOR --sim $JSON_TESTS_DIR/v1/* &> $simlog & PIDsim=$!
$JSON_TEST_SIMULATOR --cmio $JSON_TESTS_DIR/v1/* &> $cmiolog & PIDcmio=$!

echo
wait_log "CSimulator tests" $PIDcsim "(see $csimlog)"
wait_log "CCMIOSimulator tests" $PIDccmio "(see $ccmiolog)"
wait_log "Simulator tests" $PIDsim "(see $simlog)"
wait_log "CMIOSimulator tests" $PIDcmio "(see $cmiolog)"
