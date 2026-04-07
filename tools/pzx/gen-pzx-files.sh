#!/usr/bin/env bash
if [[ -z $T2SFILES_HOME ]]; then
  echo "ERROR: T2SFILES_HOME is not set"
  exit 1
fi
if [[ ! -d $T2SFILES_HOME ]]; then
  echo "ERROR: $T2SFILES_HOME: directory not found"
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
  t2sp=${t2s#$T2SFILES_HOME/t2s/}
  pzx=${t2sp%.t2s}.pzx
  if [[ -f $PZXDIR/$pzx ]]; then
    continue
  fi
  z=$(grep -oPm 1 '(spectrumcomputing.co.uk|worldofspectrum.net)/.*\.zip' $t2s)
  if [[ -n $z ]]; then
    tape_dir=$SPECTRUM_TAPES/${z%.zip}
    if [[ -d $tape_dir ]]; then
      ntapes=$(grep -c '^--tape-name' $t2s)
      [[ $ntapes -gt 1 ]] && continue
      fname=$(grep '^--tape-name' $t2s | cut -f2- -d' ' | tr -d '"')
      tape_file="$tape_dir/$fname"
      if [[ -f $tape_file ]]; then
        ext=${fname##*.}
        converter=./${ext,,}2pzx
        if [[ -f $converter ]]; then
          [[ $converter == ./tap2pzx ]] && options="-p 1000" || options=""
          echo "Writing $pzx"
          if ! $converter $options "$tape_file" > $PZXDIR/$pzx; then
            echo "Failed to convert $tape_file" >> $LOG
          fi
        else
          echo "Unrecognised tape format ($ext): $tape_file" >> $LOG
        fi
      else
        echo "$(basename $t2s): Tape file not found: $tape_file" >> $LOG
      fi
    else
      echo "$(basename $t2s): Tape directory not found: $tape_dir" >> $LOG
    fi
  fi
done

[[ -f $LOG ]] && echo "There were errors; see $LOG"
