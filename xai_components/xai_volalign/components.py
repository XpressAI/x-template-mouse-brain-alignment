from xai_components.base import InArg, OutArg, InCompArg, Component, BaseComponent, xai_component, dynalist, SubGraphExecutor

import os
import tifffile
import numpy as np
from VolAlign import *
from exm.stitching.tileset import Tileset


@xai_component(color="blue")
class CreateBDVXML(Component):
    """
    Component wrapper for VolAlign.create_bdv_xml.

    Creates a BDV/XML file for BigStitcher from a set of FOV TIFF images and their corresponding offsets.
    This component adjusts the provided column and row offsets based on unique values and writes the BDV/XML file
    using the npy2bdv library.

    ##### inPorts:
    - tiles_folder (str, compulsory): Path to the output folder where the BDV/XML file and associated tile data will be saved.
    - fov_list (list, compulsory): List of file paths to the FOV TIFF images.
    - offset_array (list of lists, compulsory): List of lists containing offsets [column, row, z] for each FOV. 
      This list is converted to a numpy array internally.
    - voxel_size (list, compulsory): Voxel size for the volume in [z, y, x] order.
    - nchannels (int): Number of channels in each FOV image. Default is 1.
    - overlap_percentage (float): Overlap percentage between the tiles. Default is 0.05.

    ##### outPorts:
    - None.
    """
    
    # Compulsory input ports
    tiles_folder: InCompArg[str]
    fov_list: InCompArg[list]
    offset_array: InCompArg[list]
    voxel_size: InCompArg[list]

    nchannels: InArg[int]
    overlap_percentage: InArg[float]
    
    def execute(self, ctx) -> None:
        # Retrieve values from compulsory ports.
        tiles_folder = self.tiles_folder.value
        fov_list = self.fov_list.value
        offset_array = np.array(self.offset_array.value)
        voxel_size = self.voxel_size.value
        
        # Retrieve optional values or fallback to defaults.
        nchannels = self.nchannels.value if self.nchannels.value is not None else 1
        increment_scale = self.overlap_percentage.value if self.overlap_percentage.value is not None else 0.05
        
        try:
            # Call the VolAlign function with the provided parameters.
            create_bdv_xml(
                tiles_folder=tiles_folder,
                fov_list=fov_list,
                offset_array=offset_array,
                voxel_size=voxel_size,
                nchannels=nchannels,
                increment_scale=increment_scale
            )
            print(f"BDV/XML file successfully created in {tiles_folder}")
        except Exception as e:
            print(f"Error during BDV/XML creation: {e}")
            raise


@xai_component(color="magenta")
class StitchTiles(Component):
    """
    Component wrapper for VolAlign.stitch_tiles.

    Executes a tile stitching pipeline by generating an ImageJ macro and running Fiji in headless mode.
    This component constructs an ImageJ macro that:
      1. Calculates pairwise shifts using phase correlation.
      2. Filters pairwise shifts based on specified criteria.
      3. Optimizes the global alignment and applies the calculated shifts.
    The macro is written to a temporary file and executed by Fiji in headless mode.

    ##### inPorts:
    - xml_file_path (str, compulsory): Path to the BDV/XML file that contains the tile configuration.
    - fiji_path (str, compulsory): Full path to the Fiji executable.

    ##### outPorts:
    - None.
    """
    
    xml_file_path: InCompArg[str]
    fiji_path: InCompArg[str]
    
    def execute(self, ctx) -> None:
        xml_file_path = self.xml_file_path.value
        fiji_path = self.fiji_path.value
        
        try:
            stitch_tiles(xml_file_path, fiji_path)
            print(f"Tile stitching executed successfully using XML: {xml_file_path} and Fiji: {fiji_path}")
        except Exception as e:
            print(f"Error during tile stitching: {e}")
            raise

@xai_component(color="green")
class BlendTiles(Component):
    """
    Component wrapper for VolAlign.blend_tiles.

    Blends stitched tile images for each channel and saves a TIFF file for each channel.
    
    This component performs the following steps:
      1. Loads a tileset from a BDV/XML file (Updated by BigStitcher) using the provided voxel size.
      2. Groups tiles into chunks of size 'num_of_tiles / num_of_channels'. Each group is assumed to correspond to one channel.
      3. For each group, computes offsets (converted to pixel units by dividing by the voxel size)
         and collects the corresponding image tiles.
      4. Blends the collected tiles using `blend_ind` to generate a single volume per channel.
      5. Saves the blended volume as a TIFF file named "stitched_{channel}.tif" in the specified output folder.

    ##### inPorts:
    - xml_file (str, compulsory): Path to the BDV/XML file generated by BigStitcher.
    - output_folder (str, compulsory): Folder where the output TIFF files will be saved.
    - voxel_size (list, compulsory): Voxel size as a list in [z, y, x] order.
    - channels_names (list, compulsory): List of channel names (e.g., ['CH1', 'CH2']).

    ##### outPorts:
    - None.
    """
    
    xml_file: InCompArg[str]
    output_folder: InCompArg[str]
    voxel_size: InCompArg[list]
    channels_names: InCompArg[list]
    
    # Optional input port with default value of None
    inverts: InArg[list]
    
    def execute(self, ctx) -> None:
        xml_file = self.xml_file.value
        output_folder = self.output_folder.value
        voxel_size = self.voxel_size.value
        channels_names = self.channels_names.value
        
        try:
            blend_tiles(
                xml_file=xml_file,
                output_folder=output_folder,
                voxel_size=voxel_size,
                channels=channels_names
            )

        except Exception as e:
            print(f"Error during tile blending: {e}")
            raise


@xai_component(color="green")
class VoxelSpacingResample(Component):
    """
    Component wrapper for VolAlign.voxel_spacing_resample.

    Loads a 3D .tif image, sets its original spacing, and resamples it to a target spacing.
    The component performs the following steps:
      1. Reads the image from the provided .tif file path.
      2. Converts the image to a SimpleITK image and casts it to uint16.
      3. Sets the image's original spacing.
      4. Computes the new image size based on the target spacing.
      5. Uses a SimpleITK resampler with the specified interpolator (default: sitk.sitkLinear)
         to adjust the image to the desired target spacing.
      6. Writes the resampled image to the specified output path.

    ##### inPorts:
    - input_file (str, compulsory): Path to the 3D .tif image file.
    - output_path (str, compulsory): Path where the resampled 3D .tif image will be saved.
    - original_spacing (list, compulsory): Original spacing in [z, y, x] order.
    - target_spacing (list, compulsory): Desired target spacing in [z, y, x] order.

    ##### outPorts:
    - None
    """
    
    # Compulsory input ports
    input_file: InCompArg[str]
    output_path: InCompArg[str]
    original_spacing: InCompArg[list]
    target_spacing: InCompArg[list]
    
    
    def execute(self, ctx) -> None:
        input_file = self.input_file.value
        output_path = self.output_path.value
        original_spacing = self.original_spacing.value
        target_spacing = self.target_spacing.value
        
        try:
            resampled = voxel_spacing_resample(
                input_file=input_file,
                output_path=output_path,
                original_spacing=original_spacing,
                target_spacing=target_spacing
            )

            print(f"Resampling completed. Resampled image saved to {output_path}")
        except Exception as e:
            print(f"Error during voxel spacing resampling: {e}")
            raise


@xai_component(color="purple")
class ApplyManualAlignment(Component):
    """
    Component wrapper for VolAlign.apply_manual_alignment.

    Aligns a moving volume to a fixed volume using an affine transformation read from a file.
    This component performs the following steps:
      1. Loads a 3×3 transformation matrix from a text file and constructs a 4×4 homogeneous transformation matrix.
      2. Reads the fixed and moving image volumes from TIFF files and converts them into SimpleITK images.
      3. Sets up an affine transform using the transformation matrix.
      4. Resamples the moving image to align it with the fixed image.
      5. Writes the resampled moving image and the fixed image to the specified output paths.

    ##### inPorts:
    - matrix_file_path (str, compulsory): Path to the text file containing a 3×3 transformation matrix.
    - fixed_volume_path (str, compulsory): Path to the fixed (reference) image volume in TIFF format.
    - moving_slice_path (str, compulsory): Path to the moving image volume in TIFF format.
    - resample_output_fixed_path (str, compulsory): Output path for writing the fixed image in TIFF format.
    - resample_output_moving_path (str, compulsory): Output path for writing the resampled moving image in TIFF format.

    ##### outPorts:
    - None.
    """
    
    matrix_file_path: InCompArg[str]
    fixed_volume_path: InCompArg[str]
    moving_volume_path: InCompArg[str]
    resample_output_fixed_path: InCompArg[str]
    resample_output_moving_path: InCompArg[str]
    
    def execute(self, ctx) -> None:
        matrix_file_path = self.matrix_file_path.value
        fixed_volume_path = self.fixed_volume_path.value
        moving_volume_path = self.moving_volume_path.value
        resample_output_fixed_path = self.resample_output_fixed_path.value
        resample_output_moving_path = self.resample_output_moving_path.value
        
        try:
            apply_manual_alignment(
                matrix_file_path=matrix_file_path,
                fixed_slice_path=fixed_volume_path,
                moving_slice_path=moving_volume_path,
                resample_output_fixed_path=resample_output_fixed_path,
                resample_output_moving_path=resample_output_moving_path
            )
            print("Alignment applied successfully.")
        except Exception as e:
            print(f"Error during alignment: {e}")
            raise


@xai_component(color="orange")
class LinearAlignmentTuning(Component):
    """
    Component wrapper for VolAlign.linear_alignment_tuning.

    Executes an alignment pipeline between fixed and moving 3D volumes and saves the resulting
    affine transformation matrix.

    The component performs the following steps:
      1. Reads two 3D TIFF volumes (fixed and moving) from the provided file paths.
      2. Prints the shapes of the input volumes for verification.
      3. Uses a customizable set of alignment steps. If no steps are provided, a default configuration is used.
      4. Calls the alignment_pipeline to compute the affine transformation matrix.
      5. Saves the computed affine transformation matrix to a text file.

    ##### inPorts:
    - fixed_path (str, compulsory): File path to the fixed TIFF volume.
    - moving_path (str, compulsory): File path to the moving TIFF volume.
    - fixed_spacing (list, compulsory): Original spacing for the fixed volume in [z, y, x] order.
    - moving_spacing (list, compulsory): Original spacing for the moving volume in [z, y, x] order.
    - output_matrix_file (str, compulsory): File path where the computed affine transformation matrix will be saved.
    - steps (list): Optional list of alignment steps. Default is None.

    ##### outPorts:
    - affine_matrix (np.ndarray): The computed affine transformation matrix.
    """
    
    fixed_path: InCompArg[str]
    moving_path: InCompArg[str]
    fixed_spacing: InCompArg[list]
    moving_spacing: InCompArg[list]
    output_matrix_file: InCompArg[str]
    
    steps: InArg[list]
    
    affine_matrix: OutArg[object]
    
    def execute(self, ctx) -> None:
        fixed_path = self.fixed_path.value
        moving_path = self.moving_path.value
        fixed_spacing = self.fixed_spacing.value
        moving_spacing = self.moving_spacing.value
        output_matrix_file = self.output_matrix_file.value
        steps = self.steps.value if self.steps.value is not None else None
        
        try:
            result = linear_alignment_tuning(
                fixed_path=fixed_path,
                moving_path=moving_path,
                fixed_spacing=fixed_spacing,
                moving_spacing=moving_spacing,
                output_matrix_file=output_matrix_file,
                steps=steps
            )
            self.affine_matrix.value = result
            print(f"Affine transformation matrix computed and saved to {output_matrix_file}")
        except Exception as e:
            print(f"Error during linear alignment tuning: {e}")
            raise


@xai_component(color="cyan")
class ConvertZarrToTiff(Component):
    """
    Component wrapper for VolAlign.convert_zarr_to_tiff.

    Converts a Zarr-formatted file to a TIFF image file.
    This component reads a dataset from a Zarr file, converts it to a NumPy array,
    and writes the array to a TIFF file using the 'minisblack' photometric convention.

    ##### inPorts:
    - zarr_file (str, compulsory): Path to the input Zarr file.
    - tiff_file (str, compulsory): Path to the output TIFF file.

    ##### outPorts:
    - None.
    """
    zarr_file: InCompArg[str]
    tiff_file: InCompArg[str]

    def execute(self, ctx) -> None:
        zarr_file = self.zarr_file.value
        tiff_file = self.tiff_file.value
        try:
            convert_zarr_to_tiff(zarr_file, tiff_file)
            print(f"Converted Zarr file {zarr_file} to TIFF file {tiff_file}")
        except Exception as e:
            print(f"Error in convert_zarr_to_tiff: {e}")
            raise


@xai_component(color="teal")
class ConvertTiffToZarr(Component):
    """
    Component wrapper for VolAlign.convert_tiff_to_zarr.

    Converts a TIFF image file to a Zarr-formatted file.
    This component reads a TIFF image file into a NumPy array and saves it in Zarr format,
    supporting multi-dimensional image data.

    ##### inPorts:
    - tiff_file (str, compulsory): Path to the input TIFF file.
    - zarr_file (str, compulsory): Path where the output Zarr file will be stored.

    ##### outPorts:
    - None.
    """
    tiff_file: InCompArg[str]
    zarr_file: InCompArg[str]

    def execute(self, ctx) -> None:
        tiff_file = self.tiff_file.value
        zarr_file = self.zarr_file.value
        try:
            convert_tiff_to_zarr(tiff_file, zarr_file)
            print(f"Converted TIFF file {tiff_file} to Zarr file {zarr_file}")
        except Exception as e:
            print(f"Error in convert_tiff_to_zarr: {e}")
            raise


@xai_component(color="brown")
class DownsampleTiff(Component):
    """
    Component wrapper for VolAlign.downsample_tiff.

    Reads a 3D TIFF image, downsamples it using specified factors and interpolation order,
    and writes the downsampled image to a new TIFF file.
    The downsampling scale is computed as the reciprocal of each provided factor.

    ##### inPorts:
    - input_path (str, compulsory): Path to the input TIFF file containing the original 3D image volume.
    - output_path (str, compulsory): Path where the downsampled TIFF image will be saved.
    - factors (tuple, compulsory): Downsampling factors for each axis (e.g., (6, 6, 6)).
    - order (int): The order of the spline interpolation used in zoom. Default is 1 (linear interpolation).

    ##### outPorts:
    - None.
    """
    input_path: InCompArg[str]
    output_path: InCompArg[str]
    factors: InCompArg[tuple]
    order: InArg[int]

    def execute(self, ctx) -> None:
        input_path = self.input_path.value
        output_path = self.output_path.value
        factors = self.factors.value
        order = self.order.value if self.order.value is not None else 1
        try:
            downsample_tiff(input_path, output_path, factors, order)
            print(f"Downsampled TIFF from {input_path} and saved to {output_path}")
        except Exception as e:
            print(f"Error in downsample_tiff: {e}")
            raise


@xai_component(color="yellow")
class StackTiffImages(Component):
    """
    Component wrapper for VolAlign.stack_tiff_images.

    Reads two TIFF files, verifies they have the same shape, stacks them along a new channel axis,
    and saves the resulting stacked image to an output file.

    ##### inPorts:
    - file1 (str, compulsory): Path to the first input TIFF file.
    - file2 (str, compulsory): Path to the second input TIFF file.
    - output_file (str, compulsory): Path where the output stacked TIFF image will be saved.

    ##### outPorts:
    - None.
    """
    file1: InCompArg[str]
    file2: InCompArg[str]
    output_file: InCompArg[str]

    def execute(self, ctx) -> None:
        file1 = self.file1.value
        file2 = self.file2.value
        output_file = self.output_file.value
        try:
            stack_tiff_images(file1, file2, output_file)
            print(f"Stacked TIFF images from {file1} and {file2} and saved to {output_file}")
        except Exception as e:
            print(f"Error in stack_tiff_images: {e}")
            raise


@xai_component(color="purple")
class ReorientVolume(Component):
    """
    Component wrapper for VolAlign.reorient_volume_and_save_tiff.

    Reads a 3D volume from a TIFF file, reorients it by applying a specified rotation (in multiples of 90°)
    and an optional flip along the first (z) axis, and saves the resulting volume as a TIFF file.

    ##### inPorts:
    - input_path (str, compulsory): Path to the input TIFF file containing the 3D volume.
    - output_path (str, compulsory): Path where the reoriented TIFF file will be saved.
    - rotation (int, compulsory): Rotation angle in degrees. Must be one of [0, 90, 180, 270].
    - flip (bool, compulsory): If True, flip the volume along the first (z) axis after rotation.

    ##### outPorts:
    - reoriented_volume (np.ndarray): The reoriented volume.
    """
    input_path: InCompArg[str]
    output_path: InCompArg[str]
    rotation: InCompArg[int]
    flip: InCompArg[bool]

    reoriented_volume: OutArg[object]

    def execute(self, ctx) -> None:
        input_path = self.input_path.value
        output_path = self.output_path.value
        rotation = self.rotation.value
        flip = self.flip.value
        try:
            result = reorient_volume_and_save_tiff(input_path, output_path, rotation, flip)
            self.reoriented_volume.value = result
            print(f"Reoriented volume from {input_path} saved to {output_path}")
        except Exception as e:
            print(f"Error in reorient_volume_and_save_tiff: {e}")
            raise