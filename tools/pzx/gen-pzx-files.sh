#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
  exit 1
fi

if [[ -z $SPECTRUM_TAPES ]]; then
  echo "ERROR: SPECTRUM_TAPES environment variable not defined"
  exit 1
fi

if [[ -d $SPECTRUM_TAPES ]]; then
  MD5SUMS=$SPECTRUM_TAPES/md5sums.txt
else
  echo "ERROR: SPECTRUM_TAPES=$SPECTRUM_TAPES: directory not found"
  exit 1
fi

if [[ ! -f tzx2pzx ]]; then
  rm -rf pzxtools pzxtools_11_src.zip
  wget http://zxds.raxoft.cz/pzx/pzxtools_11_src.zip &&
  unzip -d pzxtools pzxtools_11_src.zip &&
  patch -p1 < $SKOOLKIT_HOME/tools/pzx/pzxtools.diff &&
  make -C pzxtools/src &&
  mv pzxtools/src/{tap,tzx}2pzx .
fi

if [[ ! -f tzx2pzx ]]; then
  echo "ERROR: Failed to build tap2pzx and tzx2pzx"
  exit 1
fi

PZXDIR=pzx
LOG=gen-pzx-files.log
mkdir -p $PZXDIR/{0,a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z}
rm -f $LOG
find $T2SFILES_HOME/t2s -name '*.t2s' | while read t2s; do
  ntapes=$(grep -c '^--tape-name' $t2s)
  [[ $ntapes -gt 1 ]] && continue
  t2sp=${t2s#$T2SFILES_HOME/t2s/}
  pzx=${t2sp%.t2s}.pzx
  [[ -f $PZXDIR/$pzx ]] && continue
  md5=$(grep -oPm 1 '(?<=--tape-sum )[0-9a-f]{32}' $t2s)
  if [[ -z $md5 ]]; then
     echo "Unable to obtain tape sum from $t2s" >> $LOG
     continue
  fi
  tape_file=$(grep -oPm 1 "(?<=$md5  ).*" $MD5SUMS)
  if [[ ! -f $tape_file ]]; then
    echo "$(basename $t2s): Tape file not found: $tape_file" >> $LOG
    continue
  fi
  ext=${tape_file##*.}
  converter=./${ext,,}2pzx
  if [[ ! -f $converter ]]; then
    echo "Unrecognised tape format ($ext): $tape_file" >> $LOG
    continue
  fi
  [[ $converter == ./tap2pzx ]] && options="-p 1000" || options=""
  echo "Writing $pzx"
  if ! $converter $options "$tape_file" > $PZXDIR/$pzx; then
    echo "Failed to convert $tape_file" >> $LOG
  fi
done

[[ -f $LOG ]] && echo "There were errors; see $LOG"
