#!/usr/bin/env bash
set -e # Abort on errors

TOOLS=$(dirname $(realpath $0))
. $TOOLS/z80testrc

require_dir SKOOLKIT_HOME

EXP_MD5_SUM=89b42e717454959d5c46564fa79a97dc

cd $SKOOLKIT_HOME
rm -f hungry_horace.z80
./tap2sna.py @examples/hungry_horace.t2s
z80md5=$(md5sum hungry_horace.z80 | cut -f1 -d ' ')
if [[ $z80md5 != $EXP_MD5_SUM ]]; then
  echo -e "\n\e[0;31mERROR: MD5 sum is $z80md5; expected $EXP_MD5_SUM\e[0m"
  exit 1
fi
echo -e "\nMD5 sum OK"
rm hungry_horace.z80
