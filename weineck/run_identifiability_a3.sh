#!/bin/bash
# Identifiability addendum A3 (docs/IDENTIFIABILITY_PLAN.md): Worlds B and C, nested-lambda check, World A refinement.
# N single-threaded workers pull from a shared list (lock file); longest cells (nested) first.
# Each A3 cell uses the seed of the World A cell with the same (w, r, trials, tempi) string, so comparisons
# with World A are paired on the same trial draws and noise realisations.
cd "$(dirname "$0")"; export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
W=${1:-4}; D=results/identifiability; mkdir -p $D/logs_a3; Q=$D/a3_queue.txt; L=$D/a3_queue.lock
if [ ! -f $Q ]; then
  for w in 0 0.5 0.9 1; do echo "A nested $w 0.04 40 12 10"; done > $Q
  for wd in B C; do for w in 0 0.1 0.25 0.5 0.6 0.7 0.8 0.9 1; do echo "$wd fixed $w 0.04 40 12 20"; done; done >> $Q
  for rn in "0.08 40" "0.04 160"; do for w in 0.6 0.7 0.8 0.9; do echo "A fixed $w $rn 12 20"; done; done >> $Q
fi
worker() {
  while true; do
    cell=$(flock $L bash -c "head -1 $Q; sed -i '1d' $Q"); [ -z "$cell" ] && break
    set -- $cell; world=$1; mode=$2; w=$3; r=$4; n=$5; t=$6; nd=$7
    seed=$(( $(echo "$w $r $n $t" | cksum | cut -d" " -f1) % 100000 ))
    extra=""; [ "$mode" = "nested" ] && extra="--nested"
    python3 identifiability_sim.py --world $world $extra --w $w --r $r --trials $n --ntempi $t --datasets $nd --participants 20 --seed $seed > $D/logs_a3/${world}_${mode}_w${w}_r${r}_n${n}_t${t}.log 2>&1
  done
}
for i in $(seq 1 $W); do worker & done; wait; echo "all A3 cells done $(date)"
