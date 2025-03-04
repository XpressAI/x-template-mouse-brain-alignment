# Xircuits Mouse Brain Alignment Template

![stitch_data](https://github.com/user-attachments/assets/1d62d7cc-3a4e-4e63-8506-96eea9e365b4)

![process_data](https://github.com/user-attachments/assets/457144ff-1b75-4113-a697-c28a64c75075)



## Template Setup
You will need Python 3.10+ to install Xircuits. We recommend installing within a conda virtual environment.

## Libraries Setup
After cloning the template, install the required libraries by running:
```
$ pip install -r requirements.txt
```

# Launch
In a `srun` interactive session, activate your conda virtual environment, navigate to your template then Launch Xircuits by executing:
```
$ xircuits --ip=0.0.0.0 --port=5520 --no-browser --NotebookApp.allow_origin='*' --NotebookApp.port_retries=0
```
In a different local terminal, Run: 
```
$ ssh -L 5520:nodexxxx:5520 <user_name>@eofe10.mit.edu  #replace the xxxx with the compute node and add your user name
```
Access Xircuits on your browser
```
http://localhost:5520/
```

### More detailed information on installation, setup, and features can be found on Xircuits.

## Mouse Brain Volume Alignment
This template provides a suite of Xircuits components that assist and streamline volume alignment steps for mouse brain imaging. It encompasses several workflows covering the complete processing pipeline—from stitching raw image data to preparing aligned volumes for distributed processing.

### Workflows
1. Workflow: stitch_data.xircuits
This workflow stitches multiple Field-of-View (FOV) TIFF images into a single dataset using three key steps:


2. Workflow: preprocessing_data_invivo.xircuits
This workflow preprocesses in vivo volumes by correcting orientation and adjusting resolution for further analysis.


3. Workflow: preprocessing_data_exvivo.xircuits
This workflow preprocesses ex vivo volumes with two essential steps adjusting resolution for further analysis and downsampling.

4. Landmark Selection with Fiji BigWarp
Before alignment, use the Fiji BigWarp plugin to visually select landmarks and create the initial alignment matrices. This manual step is crucial for generating accurate affine transformations.

5. Workflow: initial_alignement.xircuits
This workflow performs initial alignment using landmark-based affine matrices (obtained from Fiji BigWarp) on both downsampled and full-size volumes:

Downsampled Volume Alignment:
Applies the manually selected (landmark-based) affine matrix to the downsampled volume, executes alignment tuning on the downsampled volumes to compute a refined affine matrix that will assist in later non-linear deformation alignment.
Full-Size Volume Alignment.

6. Distributed Alignment (Shell Script)
Note: This step is not yet integrated into Xircuits. It involves editing the shell script `alignment_sbatch_final.sh` to use sbatch for submitting distributed jobs to a cluster. 

Notice
This is still work-in-progress feel free to raise any issue you face. 
