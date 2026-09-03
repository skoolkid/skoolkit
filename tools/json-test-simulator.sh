#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

require_dir SKOOLKIT_HOME
require_env SPECTRUM_JSON_TESTS

JSON_TEST_SIMULATOR="$TOOLS/json-test-simulator.py"

make -C $SKOOLKIT_HOME cmods

if [[ ! -d $SPECTRUM_JSON_TESTS ]]; then
  git clone https://github.com/SingleStepTests/z80.git $SPECTRUM_JSON_TESTS
fi

csimlog="$SPECTRUM_JSON_TESTS/json-test-simulator-csim.log"
ccmiolog="$SPECTRUM_JSON_TESTS/json-test-simulator-ccmio.log"
simlog="$SPECTRUM_JSON_TESTS/json-test-simulator-sim.log"
cmiolog="$SPECTRUM_JSON_TESTS/json-test-simulator-cmio.log"

$JSON_TEST_SIMULATOR --csim $SPECTRUM_JSON_TESTS/v1/* &> $csimlog & PIDcsim=$!
$JSON_TEST_SIMULATOR --ccmio $SPECTRUM_JSON_TESTS/v1/* &> $ccmiolog & PIDccmio=$!
$JSON_TEST_SIMULATOR --sim $SPECTRUM_JSON_TESTS/v1/* &> $simlog & PIDsim=$!
$JSON_TEST_SIMULATOR --cmio $SPECTRUM_JSON_TESTS/v1/* &> $cmiolog & PIDcmio=$!

echo
wait_log "CSimulator tests" $PIDcsim "(see $csimlog)" || rc=1
wait_log "CCMIOSimulator tests" $PIDccmio "(see $ccmiolog)" || rc=1
wait_log "Simulator tests" $PIDsim "(see $simlog)" || rc=1
wait_log "CMIOSimulator tests" $PIDcmio "(see $cmiolog)" || rc=1

exit ${rc:-0}
