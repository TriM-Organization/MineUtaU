#!/bin/bash
#SBATCH --job-name=extract_fsb_mpi
#SBATCH --output=extract_fsb_mpi.%j.out
#SBATCH --error=extract_fsb_mpi.%j.err
#SBATCH --ntasks=16
#SBATCH --nodes=4
#SBATCH --time=02:00:00
#SBATCH --partition=apollo
#SBATCH --mem=8G

module load compiler/intel/2021.3.0
module load mpi/intelmpi/2021.3.0
module load miniconda3.2025
source /share/software/miniconda3.2025/bin/activate
conda activate mpi_2025_demo

mpirun -n $SLURM_NTASKS python ./main.py

echo "已完成全部任务。"
