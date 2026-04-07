#!/usr/bin/env bash
if [[ -z $SPECTRUM_RZX ]]; then
  echo "ERROR: SPECTRUM_RZX is not set"
  exit 1
fi
if [[ ! -d $SPECTRUM_RZX ]]; then
  echo "ERROR: $SPECTRUM_RZX: directory not found"
  exit 1
fi

usage() {
  cat <<EOF
Usage: $(basename $0) FILE

  Find RZX files not yet listed in rzx-work.txt or rzx-fail.txt and write them
  to FILE.
EOF
  exit 1
}

[[ -z $1 ]] && usage

WORK=$SKOOLKIT_HOME/tools/rzx/rzx-work.txt
FAIL=$SKOOLKIT_HOME/tools/rzx/rzx-fail.txt

allrzx=$(mktemp)
pushd "$SPECTRUM_RZX" > /dev/null
find -iname '*.rzx' -type f | cut -c3- | sort > "$allrzx"
popd > /dev/null

workfail=$(mktemp)
cut -f1 -d\| $WORK $FAIL | sort > "$workfail"
comm -23 "$allrzx" "$workfail" > "$1"
rm -f "$allrzx" "$workfail"
echo "Wrote $1"
