#!/bin/bash
#SBATCH --time 24:59:00          
#SBATCH -N 1                 
#SBATCH -n 94               
#SBATCH --mem-per-cpu 6GB
#SBATCH --partition pi_edboyden 



# Source the Conda environment setup directly from your .bashrc's configuration
source /orcd/data/edboyden/001/mansour/miniconda3/etc/profile.d/conda.sh # change to you bashrc path
conda activate exm_dev2 # change to your conda env 


# Run the Python script with all the required arguments
python alignment_script_final.py \
    --fix_image_path "/orcd/data/edboyden/001/clarenz/SiRIs_data_mansour/MFlNSG6f_02/raw/LA_site1/processed/results/sampled_fixed_fov1_ch2.zarr" \
    --move_image_path "/orcd/data/edboyden/001/clarenz/SiRIs_data_mansour/MFlNSG6f_02/raw/LA_site1/processed/results/sampled_moving_fov1_ch2.zarr" \
    --spacing 0.1507417 0.1507417 0.1507417 \
    --blocksize 512 512 512 \
    --init_transform_path "/orcd/data/edboyden/001/clarenz/SiRIs_data_mansour/MFlNSG6f_02/raw/LA_site1/processed/results/matrix_affine_fov1.txt" \
    --output_dir "/orcd/data/edboyden/001/clarenz/SiRIs_data_mansour/MFlNSG6f_02/raw/LA_site1/processed/results/" \
    --output_name "aligned_exvivo_fov1_ch2" > final_alignment_output.log 2>&1
