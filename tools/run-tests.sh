#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

require_dir SKOOLKIT_HOME

declare -A SUITES SUITE_NAMES NOSE2_SUITES
declare -a SUITES_IN_ORDER

add_suite() {
  local suite=$1
  local cmd=$2
  local name=$3

  SUITES["$suite"]="$cmd"
  SUITE_NAMES["$suite"]="$name"
  SUITES_IN_ORDER+=("$suite")
}

add_suite cover "tools/check-coverage.sh" "coverage tests"
add_suite unit "$(echo make test{,-c}-3{10,11,12,13,14}-all)" "all unit tests"
add_suite slow "make test-slow test-c-slow" "slow tests"
add_suite capi "make test-c-api" "CSimulator API tests"
add_suite json "tools/json-test-simulator.sh" "Z80 JSON tests"
add_suite flags "tools/z80-flags-test.sh" "Z80 flags test"
add_suite z80doc "tools/z80-test-simulator.sh" "Z80 doc test"
add_suite memptr "tools/z80-memptr-tests.sh" "Z80 MEMPTR test"
add_suite timing "tools/z80-timing-tests.sh" "Z80 timing tests"
add_suite ccmiot "make test-c-cmio" "CCMIOSimulator timing tests"
add_suite cmiot "make test-cmio" "CMIOSimulator timing tests"
add_suite rzxc "tools/rzx/run-rzx-tests.sh -c" "RZX tests with CSimulator"
add_suite rzxp "tools/rzx/run-rzx-tests.sh" "RZX tests with Simulator"
add_suite t2sc "tools/run-t2sfile-tests.sh -c" "t2s file tests with CSimulator"
add_suite t2sp "tools/run-t2sfile-tests.sh" "t2s file tests with Simulator"
add_suite pzxc "tools/pzx/run-pzx-tests.sh -c" "PZX tests with CSimulator"
add_suite pzxp "tools/pzx/run-pzx-tests.sh" "PZX tests with Simulator"
add_suite hht2s "tools/check-hh-t2s.sh" "Hungry Horace t2s file test"
add_suite dtests "tools/skrelease dtests" "disassemblies tests"
add_suite api "tools/test-api" "SkoolKit API tests"
add_suite pipes "tools/test-pipes" "SkoolKit command stdin tests"
add_suite ddiffs "tools/skrelease ddiffs" "disassembly-diff"
add_suite asmchk "tools/skrelease asmchk" "check-asms"
add_suite binchk "tools/skrelease binchk" "check-bins"
add_suite pipin1 "tools/skrelease pipin1" "'pip install .' from release tarball"
add_suite pipin2 "tools/skrelease pipin2" "'pip install .' from source tarball"

NOSE2_SUITES=(
  [rzxc]=1
  [rzxp]=1
  [t2sc]=1
  [t2sp]=1
  [pzxc]=1
  [pzxp]=1
)

banner() {
  text=$1
  template="----------------------------------------"
  padding=${template:0:$(((78 - ${#text}) / 2))}
  banner_text="$padding $text $padding"
  while [ ${#banner_text} -lt 80 ]; do
    banner_text="${banner_text}${template:0:1}"
  done
  border="--------------------------------------------------------------------------------"
  echo -e "\e[0;33m$border"
  echo -e "$banner_text"
  echo -e "$border\e[0m"
}

usage() {
  cat <<EOU1
Usage: $(basename $0) [options] SUITE [SUITE...]

  Run SkoolKit pre-release tests. SUITE must be one of the following:

EOU1

  for v in ${SUITES_IN_ORDER[@]}; do
    echo "$v - ${SUITE_NAMES[$v]}"
  done | column -tl 2 | sed 's/^/    /'

  cat <<EOU2

  or 'all' for all test suites.

Options:
  -j PROCS  Run nose2 test suites using this many processes (default: $CORES).
EOU2
  exit 1
}

CORES=$(lscpu -p=SOCKET,CORE | grep -v '^#' | sort -u | wc -l)
PROCS=$CORES
while getopts ":j:" opt; do
  case $opt in
    j) PROCS=$OPTARG ;;
    *) usage ;;
  esac
done

shift $((OPTIND - 1))
[ $# -lt 1 ] && usage

if [[ $1 == "all" ]]; then
  suites=${SUITES_IN_ORDER[@]}
else
  suites=$*
fi

for suite in $suites; do
  if [[ -z ${SUITES[$suite]} ]]; then
    echo "ERROR: Unknown test suite '$suite'"
    exit 1
  fi
  if [[ -z ${SUITE_NAMES[$suite]} ]]; then
    echo "ERROR: Test suite '$suite' has no name"
    exit 1
  fi
done

cd $SKOOLKIT_HOME
for suite in $suites; do
  cmd=${SUITES[$suite]}
  name=${SUITE_NAMES[$suite]}
  banner "Running $name"
  if [[ -n ${NOSE2_SUITES[$suite]} ]]; then
    cmd="$cmd -j $PROCS"
  fi
  $cmd
done
