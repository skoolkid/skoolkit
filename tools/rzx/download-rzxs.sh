#!/usr/bin/env bash
if [[ -z $T2SFILES_USER_AGENT ]]; then
  echo "ERROR: T2SFILES_USER_AGENT is not set"
  exit 1
fi

if [[ -z $ZXDB ]]; then
  echo "ERROR: ZXDB is not set"
  exit 1
fi
if [[ ! -f $ZXDB ]]; then
  echo "ERROR: $ZXDB: file not found"
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

query="SELECT d.file_link \
FROM downloads d, entries e \
WHERE d.entry_id = e.id \
AND (e.availabletype_id NOT IN ('D', 'S') OR e.availabletype_id IS NULL) \
AND d.filetype_id = 63 \
AND d.file_link like '/zxdb/%'"

failed_log="$(pwd)/failed.log"
pause=1
first=1
rm -f "$failed_log"
cd $SPECTRUM_RZX || exit 1
sqlite3 $ZXDB "$query" | cut -c 2- | while read path; do
  if [[ ! -f $path ]]; then
    if [[ $first == 0 ]]; then
      echo -e "Waiting $pause seconds...\n"
      sleep $pause
    fi
    first=0
    mkdir -p $(dirname "$path")
    url="https://spectrumcomputing.co.uk/${path}"
    if ! wget --user-agent "$T2SFILES_USER_AGENT" -O "$path" "$url"; then
      rm -v "$path"
      echo "$path" >> "$failed_log"
    fi
  fi
done

if [[ -f $failed_log ]]; then
  failed=$(wc -l < "$failed_log")
  echo "WARNING: $failed download(s) failed; see $failed_log"
fi
