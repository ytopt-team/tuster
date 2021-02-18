#!/bin/sh

#SBATCH --job-name={{ job_name }}
#SBATCH --account={{ account }}
#SBATCH --partition={{ partition }}
#SBATCH --nodes={{ nodes }}
#SBATCH --ntasks-per-node={{ ntasks_per_node }}
#SBATCH --output={{ output }}
#SBATCH --error={{ error }}
#SBATCH --time={{ time }}


module load anaconda3/5.2.0

# export MPICH_GNI_FORK_MODE=FULLCOPY # otherwise, fork() causes segfaults above 1024 nodes
export PMI_NO_FORK=1 # otherwise, mpi4py-enabled Python apps with custom signal handlers do not respond to sigterm
export KMP_AFFINITY=disabled # this can affect on-node scaling (test this)

# Required for Click_ to work: https://click.palletsprojects.com/en/7.x/python3/
export LC_ALL=C.UTF-8
export LANG=C.UTF-8


export PATH={{ python_bin }}:$PATH

# deactivate core dump (comment for debug)
ulimit -c 0

# Start cluster
srun -n {{ n }}  python -m tuster.system.bebop.run '{{ exe }}'

