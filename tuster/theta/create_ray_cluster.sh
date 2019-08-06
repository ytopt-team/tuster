#!/bin/sh
#COBALT -A datascience
#COBALT -n 2
#COBALT -q debug-cache-quad
#COBALT -t 30

module unload trackdeps
module unload darshan
module unload xalt
# export MPICH_GNI_FORK_MODE=FULLCOPY # otherwise, fork() causes segfaults above 1024 nodes
export PMI_NO_FORK=1 # otherwise, mpi4py-enabled Python apps with custom signal handlers do not respond to sigterm
export KMP_AFFINITY=disabled # this can affect on-node scaling (test this)

# Required for Click_ to work: https://click.palletsprojects.com/en/7.x/python3/
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Activate good python environment
source /projects/datascience/regele/dh-opt/bin/activate

# Start cluster
aprun -n $COBALT_JOBSIZE -N 1  python /projects/datascience/regele/tuning-scripts/m1/go_ray.py

