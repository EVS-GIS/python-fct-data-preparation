
from fct.raster_tools import CreateTilesetFromRasters, ExtractRasterTilesFromTileset
from fct.vector_tools import ExtractByBoundMask, ExtractBylocation
from config.config import paths_config, parameters_config
import subprocess

# parameters
paths = paths_config()
params = parameters_config()

# create dem and landuse tileset

CreateTilesetFromRasters(
    input_dir_path = paths['inputs_dir_landuse_tiles'],
    extension = params['landuse_extension'],
    tileset_path = paths['tileset_landuse'],
    crs = params['crs']
)

CreateTilesetFromRasters(
    input_dir_path = paths['inputs_dir_dem_tiles'],
    extension = params['dem_extension'],
    tileset_path = paths['tileset_dem'],
    crs = params['crs']
)

# get intersection between mask and tileset

ExtractBylocation(paths['tileset_landuse'], paths['mask'], paths['tileset_mask_landuse'], method = 'intersects')
ExtractBylocation(paths['tileset_dem'], paths['mask'], paths['tileset_mask_dem'], method = 'intersects')

# copy raster tiles

ExtractRasterTilesFromTileset(
    tileset_path = paths['tileset_mask_landuse'],
    raster_dir = paths['inputs_dir_landuse_tiles'],
    dest_dir = paths['outputs_dir_landuse_tiles']
)

ExtractRasterTilesFromTileset(
    tileset_path = paths['tileset_mask_dem'],
    raster_dir = paths['inputs_dir_dem_tiles'],
    dest_dir = paths['outputs_dir_dem_tiles']
)

# create virtual raster

bash_landuse = 'gdalbuildvrt "{}" "{}"*"{}"'.format(paths['landuse_vrt'], paths['outputs_dir_landuse_tiles'], params['landuse_extension'])
vrt_landuse = subprocess.run(bash_landuse, shell=True, capture_output=True, text=True)

bash_dem = 'gdalbuildvrt "{}" "{}"*"{}"'.format(paths['dem_vrt'], paths['outputs_dir_dem_tiles'], params['dem_extension'])
vrt_dem = subprocess.run(bash_dem, shell=True, capture_output=True, text=True)

# extract hydro network from mask with contains

ExtractBylocation(paths['hydro_network'], paths['mask'], paths['hydro_network_mask'], method = 'contains')

