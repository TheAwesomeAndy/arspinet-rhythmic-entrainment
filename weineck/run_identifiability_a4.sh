#!/bin/bash
# Identifiability addendum A4 (docs/IDENTIFIABILITY_PLAN.md): nested-lambda cells (A4.1, A4.2) and lambda-pair reruns (A4.2).
# Seeds as in A3: the World A cell string "$w 0.04 40 12", so the simulated datasets are the A3 datasets.
cd "$(dirname "$0")"; export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
W=${1:-4}; D=results/identifiability; mkdir -p $D/logs_a4; Q=$D/a4_queue.txt; L=$D/a4_queue.lock
if [ ! -f $Q ]; then
  for w in 0.6 0.7 0.8; do echo "A nested $w 10"; done > $Q
  for w in 0.6 0.7 0.8 0.9 1; do echo "C nested $w 10"; done >> $Q
  for wd in A C; do for w in 0.8 0.9 1; do echo "$wd lampair $w 20"; done; done >> $Q
fi
worker() {
  while true; do
    cell=$(flock $L bash -c "head -1 $Q; sed -i '1d' $Q"); [ -z "$cell" ] && break
    set -- $cell; world=$1; mode=$2; w=$3; nd=$4
    seed=$(( $(echo "$w 0.04 40 12" | cksum | cut -d" " -f1) % 100000 ))
    python3 identifiability_sim.py --world $world --$mode --w $w --r 0.04 --trials 40 --ntempi 12 --datasets $nd --participants 20 --seed $seed > $D/logs_a4/${world}_${mode}_w${w}.log 2>&1
  done
}
for i in $(seq 1 $W); do worker & done; wait; echo "all A4 cells done $(date)"
