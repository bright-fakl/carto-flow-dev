#!/bin/bash
# repeated timings on a quiet machine: input x method x 3 repeats, n_iter 3000, records in protocol.jsonl (proto t)
cd /tmp/claude-1000/-home-fakl-carto-flow/ede8c6da-5d47-4428-a510-9e1f1953f075/scratchpad/validity
export PROTO=t1
run() { # input-label dataset method rep
  local lab=$1 ds=$2 m=$3 rep=$4
  case $m in
    base) cmd="runall.py"; export HOOK=none;;
    vw10) cmd="runall.py"; export HOOK=vw EVERY=10 STOPR=3 MINLEN=1e-6 SKIPS=1;;
    q1) cmd="pwo_run.py"; export REBUILD=1 MINRATIO=0 BITS=6 PEVERY=1;;
    q4) cmd="pwo_run.py"; export REBUILD=4 MINRATIO=0.6 BITS=6 PEVERY=1;;
    q8) cmd="pwo_run.py"; export REBUILD=8 MINRATIO=0.6 BITS=6 PEVERY=1;;
  esac
  METHOD=${lab}_$m LABEL=t1_${lab}_${m}_$rep ./run.sh $cmd $ds 1000 2>&1 | tail -1 | cut -c1-110
  unset HOOK EVERY STOPR MINLEN SKIPS REBUILD MINRATIO BITS PEVERY
}
for rep in 1 2 3; do
  for m in ${METHODS:-q4 q8 q1}; do
    for inp in ${INPUTS:-county cd coarse mid2000 mid3000}; do
      case $inp in
        county) unset MSEG; run county county $m $rep;;
        cd) unset MSEG; [ $m = vw10 ] && run cd cd $m $rep || run cd cd $m $rep;;
        coarse) [ $m = vw10 ] && continue; unset MSEG; run coarse coarse $m $rep;;
        mid2000) export MSEG=2000; run mid2000 mid $m $rep;;
        mid3000) export MSEG=3000; run mid3000 mid $m $rep;;
      esac
    done
  done
done
