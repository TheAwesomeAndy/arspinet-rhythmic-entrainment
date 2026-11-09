#!/bin/bash
# Lock-file queue over robustness rows: several runners can be started; each row runs once.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
F=/tmp/claude-0/-home-user/c557f3fa-3171-5dba-9414-075b9367c65c/scratchpad/weineck/small/SourceData__Figure1_SourceData1.mat
R=/home/user/arspinet-rhythmic-entrainment/weineck/results/robustness; mkdir -p $R
for row in baseline seed7 seed99 rho0 rho0.3 rho1.2 beta0.01 beta0.004 trf_flux trf_long iaaft; do
  mkdir "$R/.lock_$row" 2>/dev/null || continue
  nice -n 5 python3 /home/user/arspinet-rhythmic-entrainment/weineck/robustness.py --row $row --feats $F > "$R/$row.log" 2>&1
done
