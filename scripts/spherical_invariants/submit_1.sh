#!/bin/bash
#SBATCH --chdir /scratch/musil/rascal_benchmarks/scripts/spherical_invariants
#SBATCH --nodes 1
#SBATCH --ntasks 1
#SBATCH --cpus-per-task 3
#SBATCH --mem 180000
#SBATCH --time 16:00:00


conda activate rascal_benchmark

python project.py run -f name molecular_crystals --parallel 3 --progress  2>&1 | tee status_1.txt
