import argparse
import tifffile
import zarr
import numpy as np
from scipy.ndimage import zoom
from bigstream.align import alignment_pipeline
from bigstream.transform import apply_transform
from bigstream.piecewise_align import distributed_piecewise_alignment_pipeline
from bigstream.piecewise_transform import distributed_apply_transform

def main():
    # Initialize command-line argument parsing.
    # This section sets up the framework to accept input parameters for the alignment process,
    # including directories, numerical parameters for processing, and output paths.
    parser = argparse.ArgumentParser(description='Align two microscopy image rounds.')
    parser.add_argument('--fix_image_path', type=str, help='Path to the Fix image .zarr file')
    parser.add_argument('--move_image_path', type=str, help='Path to the Move image .zarr file')
    parser.add_argument('--spacing', nargs=3, type=float, default=[0.1507417, 0.1507417, 0.1507417], help='Voxel spacing in z, y, x dimensions (in microns)')
    parser.add_argument('--blocksize', nargs=3, type=int, default=[512, 512, 512], help='Size of blocks for piecewise alignment, in z, y, x dimensions')
    parser.add_argument('--init_transform_path', type=str, help='Path to the intial alignment matrix.txt file')
    parser.add_argument('--output_dir', type=str, help='Path to directory save deformation field and alignment results')
    parser.add_argument('--output_name', type=str, help='File Name for alignment results')
    
    # Parsing command-line arguments to use in the script.
    args = parser.parse_args()
    
    # Assigning parsed arguments to variables for easier access.
    # This includes paths, numerical parameters for image processing, and flags for evaluation.
    fix_image_path = args.fix_image_path
    move_image_path = args.move_image_path  
    spacing = np.array(args.spacing)
    blocksize = args.blocksize
    init_matrix_path = args.init_transform_path
    output_dir = args.output_dir
    output_name = args.output_name

    fix_image = zarr.open(fix_image_path, mode='r') 
    move_image = zarr.open(move_image_path, mode='r') 

    cluster_config = {
        "n_workers": 16,
        "threads_per_worker": 1,
        "memory_limit": '70GB',
        'config': {
            'distributed.nanny.pre-spawn-environ': {
                'MALLOC_TRIM_THRESHOLD_': 65536,
                'MKL_NUM_THREADS': 6,
                'OMP_NUM_THREADS': 6,
                'OPENBLAS_NUM_THREADS': 6,
            },
            'distributed.scheduler.worker-ttl': None
        }
    } 
    
    
    affine = np.loadtxt(init_matrix_path)
    
    
    deform_kwargs = {
        'alignment_spacing':0.4,
        'smooth_sigmas': (0,),
        'control_point_spacing': 100.0,
        'control_point_levels': (1,),
    }
    
    
    # define the alignment steps
    steps = [('deform', deform_kwargs)]
    
    
    deform = distributed_piecewise_alignment_pipeline(
        fix_image,move_image,
        spacing, spacing,
        steps,
        blocksize=blocksize,
        overlap = 0.3,
        rebalance_for_missing_neighbors=True,
        write_path=f'{output_dir}/{output_name}_deformation_field.zarr',
        static_transform_list=[affine],
        cluster_kwargs=cluster_config,
    )

    print("deform done")
    
    # deform = zarr.open("/orcd/data/edboyden/001/clarenz/SiRIs_data_mansour/MFlNSG6f_02/raw/LA_site1/processed/results/aligned_exvivo_fov1_ch1_deformation_field.zarr/")

    cluster_config = {
        "n_workers": 8,
        "threads_per_worker": 1,
        "memory_limit": '140GB',
        'config': {
            'distributed.nanny.pre-spawn-environ': {
                'MALLOC_TRIM_THRESHOLD_': 65536,
                'MKL_NUM_THREADS': 6,
                'OMP_NUM_THREADS': 6,
                'OPENBLAS_NUM_THREADS': 6,
            },
            'distributed.scheduler.worker-ttl': None
        }
    } 

    aligned = distributed_apply_transform(
            fix_image,move_image,
            spacing, spacing,
            transform_list=[affine,deform],
            blocksize=blocksize,
            write_path=f'{output_dir}/{output_name}_aligned_round.zarr',
            cluster_kwargs=cluster_config,
        )

if __name__ == '__main__':
    main()
