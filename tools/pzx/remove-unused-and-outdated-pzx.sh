#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

find pzx -name '*.pzx' | while read p; do
  t=${p#pzx/}
  t2s=$T2SFILES_HOME/t2s/${t%.pzx}.t2s
  z=snapshots/$(basename $p .pzx).z80
  if [[ -f $t2s ]]; then
    [[ $p -ot $t2s ]] && rm -v $p
    [[ -f $z ]] && [[ $z -ot $t2s ]] && rm -v $z
  else
    rm -fv $p $z
  fi
done
