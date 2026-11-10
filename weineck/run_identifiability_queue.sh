#!/bin/bash
# Identifiability map: run every cell of docs/IDENTIFIABILITY_PLAN.md with N single-threaded workers pulling
# from a shared list (lock file). Weineck's operating point (r 0.04, 40 trials, 12 tempi) is queued first.
# Usage: bash run_identifiability_queue.sh [workers]
cd "$(dirname "$0")"; export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
W=${1:-4}; D=results/identifiability; mkdir -p $D/cells $D/logs; Q=$D/queue.txt; L=$D/queue.lock
if [ ! -f $Q ]; then
  for w in 0 0.1 0.25 0.5 1; do echo "$w 0.04 40 12"; done > $Q
  for r in 0.02 0.04 0.08 0.16; do for n in 20 40 80 160; do for w in 0 0.1 0.25 0.5 1; do
    [ "$r" = "0.04" ] && [ "$n" = "40" ] && continue; echo "$w $r $n 12"; done; done; done >> $Q
  for t in 4 8; do for w in 0 0.1 0.25 0.5 1; do echo "$w 0.04 40 $t"; done; done >> $Q
fi
worker() {
  while true; do
    cell=$(flock $L bash -c "head -1 $Q; sed -i '1d' $Q"); [ -z "$cell" ] && break
    set -- $cell; out=$D/cells/w$1_r$2_n$3_t$4.json
    if [ -f "$out" ] && python3 -c "import json,sys; d=json.load(open('$out')); sys.exit(0 if d['datasets_done']>=20 else 1)"; then continue; fi
    python3 identifiability_sim.py --w $1 --r $2 --trials $3 --ntempi $4 --datasets 20 --participants 20 --seed $(( $(echo "$cell" | cksum | cut -d" " -f1) % 100000 )) > $D/logs/w$1_r$2_n$3_t$4.log 2>&1
  done
}
for i in $(seq 1 $W); do worker & done; wait; echo "all cells done $(date)"
