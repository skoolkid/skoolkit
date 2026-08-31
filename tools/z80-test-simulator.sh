#!/usr/bin/env bash
set -e # Abort on errors

_wait() {
  message=$1
  pid=$2
  suffix=$3

  echo -n "${message}: "
  if wait $pid; then
    echo "OK $suffix"
  else
    echo -e "\e[0;31mFAILED $suffix\e[0m"
  fi
}

if [[ -z $SKOOLKIT_HOME ]]; then
  echo "ERROR: SKOOLKIT_HOME is not set"
  exit 1
fi
if [[ ! -d $SKOOLKIT_HOME ]]; then
  echo "ERROR: $SKOOLKIT_HOME: directory not found"
  exit 1
fi

TEST_SIMULATOR="$SKOOLKIT_HOME/tools/z80-test-simulator.py"

if [[ -z $SPECTRUM_SIM_TESTS ]]; then
  echo "ERROR: SPECTRUM_SIM_TESTS is not set"
  exit 1
fi
mkdir -p "$SPECTRUM_SIM_TESTS"

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
_wait "CSimulator tests" $PIDcsim "(see $csimlog)"
_wait "CCMIOSimulator tests" $PIDccmio "(see $ccmiolog)"
_wait "Simulator tests" $PIDsim "(see $simlog)"
_wait "CMIOSimulator tests" $PIDcmio "(see $cmiolog)"
