#!/usr/bin/env bash
if [[ -z $SKOOLKIT_HOME ]]; then
  echo "ERROR: SKOOLKIT_HOME is not set"
  exit 1
fi
if [[ ! -d $SKOOLKIT_HOME ]]; then
  echo "ERROR: $SKOOLKIT_HOME: directory not found"
  exit 1
fi

if [[ -z $SPECTRUM_RZX ]]; then
  echo "ERROR: SPECTRUM_RZX is not set"
  exit 1
fi
if [[ ! -d $SPECTRUM_RZX ]]; then
  echo "ERROR: $SPECTRUM_RZX: directory not found"
  exit 1
fi

UNZIP=$SKOOLKIT_HOME/tools/rzx/unzip.py

force=0
if [[ $1 == --force ]]; then
  force=1
elif [[ -n $1 ]]; then
  echo "Usage: $(basename $0) [--force]"
  echo
  echo "Extract all zip archives not yet extracted. If '--force' is used, previously"
  echo "extracted zip archives are re-extracted."
  exit 1
fi

error_log=unzip-errors.log
>$error_log

find $SPECTRUM_RZX -name '*.zip' | while read z; do
  zdir=${z%.zip}
  if [[ $force == 1 ]] || [[ ! -d $zdir ]]; then
    rm -rf "$zdir"
    mkdir "$zdir"
    if ! $UNZIP "$z" "$zdir"; then
      echo "Failed to extract $z" >> $error_log
      rm -rf "$zdir"
    fi
  fi
done

if [[ -s $error_log ]]; then
  echo -e "\nFailed to extract some zip archives; see $error_log"
else
  rm -f $error_log
fi
