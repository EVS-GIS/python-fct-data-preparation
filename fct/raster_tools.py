# coding: utf-8

"""
DOCME

***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

# packages
import rasterio
from rasterio.merge import merge
from rasterio.mask import mask
import glob
import os
import fiona
from shapely.geometry import shape
import fct.utils

from config.config import paths_config, parameters_config
import subprocess


paths = paths_config()
params = parameters_config()


def fit_raster_pixel (raster_to_fit, reference_raster, output_raster):
    
    ref_raster = rasterio.open(reference_raster)

    command = 'gdalwarp -te {} {} {} {} "{}" "{}" '.format(
        ref_raster.bounds[0], ref_raster.bounds[1], ref_raster.bounds[2], ref_raster.bounds[3], raster_to_fit, output_raster)
    
    fct.utils.process_with_stdout(command)
    


def merge_raster_in_folder(
        input_raster_folder_path: str,
        output_merge_raster_folder_path: str,
        extension: str,
        compress: str = 'deflate',
        zlevel: int = 9):
    """
    Merge all the raster file contain in a folder in Gtiff
    documentation : https://automating-gis-processes.github.io/CSC18/lessons/L6/raster-mosaic.html
    """
    # Make a search criteria to select the tiff raster files
    search_criteria = '*'+extension

    q = os.path.join(input_raster_folder_path, search_criteria)

    # list all raster file
    rasterInFolder = glob.glob(q)

    # create an empty list to gather the list of the raster name
    rasterListToMerge = []

    # read all the raster with rasterio and add it to the rasterListToMerge list
    for raster in rasterInFolder:
        item = rasterio.open(raster)
        rasterListToMerge.append(item)

    # Merge function
    mergeRaster, mergeRaster_trans = merge(datasets = rasterListToMerge, method='max')

    # Copy the metadata
    out_meta = rasterListToMerge[0].meta.copy()

    # Update the metadata
    out_meta.update({"driver": 'GTiff',
                    "height": mergeRaster.shape[1],
                    "width": mergeRaster.shape[2],
                    "transform": mergeRaster_trans,
                    "compress": compress,
                    "zlevel": zlevel
                    }
                    )
    
    # Write the mosaic raster to disk
    with rasterio.open(output_merge_raster_folder_path + 'merge_raster.tif', "w", **out_meta) as dest:
        dest.write(mergeRaster)

def CreateTilesetFromRasters(
        input_dir_path: str,
        extension: str,
        tileset_path: str,
        crs: str = '2154'):
    
    schema = { 
    'geometry': 'Polygon', 
    'properties': {'GID': 'int',
                    'NAME': 'str',
                    'X0': 'float',
                    'Y0': 'float'} }
    
    options = dict(
        driver='GPKG',
        schema=schema,
        crs=fiona.crs.from_epsg(crs))

    # Make a search criteria to select the tiff raster files
    search_criteria = '*'+extension

    q = os.path.join(input_dir_path, search_criteria)

    # list all raster file
    rasterInFolder = glob.glob(q)

    gid = 1
    with fiona.open(tileset_path, 'w', **options) as dst:
        # read all the raster with rasterio and add it to the rasterListToMerge list
        for raster in rasterInFolder:
            with rasterio.open(raster) as src:
                minx, miny, maxx, maxy = src.bounds
                coordinates = [(minx,miny), (minx,maxy), (maxx,maxy), (maxx,miny)]
                # Define the feature properties and geometry.
                feature = {
                    'geometry': {
                        'type':'Polygon',
                        'coordinates': [coordinates] 
                    },
                    'properties': {
                        'GID': gid,
                        'NAME': os.path.basename(raster),
                        'Y0': minx,
                        'X0': miny
                    }
                }
            # Write only features that intersect with the study area.
            dst.write(feature)
            gid += 1
            
def ExtractRasterTilesFromTileset(
        tileset_path,
        raster_dir,
        dest_dir):
    
    with fiona.open(tileset_path) as src:
        for feature in src : 
            filename = feature['properties']['NAME']
            raster_file = os.path.join(raster_dir, filename)
            dest_file = os.path.join(dest_dir, filename)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            # Ouvre le fichier source en mode lecture binaire
            with open(raster_file, "rb") as src_file:
                # Ouvre le fichier de destination en mode écriture binaire
                with open(dest_file, "wb") as dest_file:
                    # Lit le contenu du fichier source et écrit dans le fichier de destination
                    dest_file.write(src_file.read())

def ClipRasterByPolygon(raster_path, polygon_path, output_raster_path):
    with fiona.open(polygon_path, "r") as poly:
        feature = shape(poly['geometry'])

        with open(raster_path) as src:
            out_image, out_transform = rasterio.mask.mask(src, feature, crop=True)
            out_meta = src.meta

            out_meta.update({"driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform})
            
        with rasterio.open(output_raster_path, "w", **out_meta) as dest:
            dest.write(out_image)
