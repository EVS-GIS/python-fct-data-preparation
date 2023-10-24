
import config.config
import fct.raster_tools
import fct.vector_tools
import fct.utils

# parameters
paths = config.config.paths_config()
params = config.config.parameters_config()

# create dem and landuse tileset
fct.raster_tools.CreateTilesetFromRasters(
    input_dir_path = paths['inputs_dir_landuse_tiles'],
    extension = params['landuse_extension'],
    tileset_path = paths['tileset_landuse'],
    crs = params['crs']
)

fct.raster_tools.CreateTilesetFromRasters(
    input_dir_path = paths['inputs_dir_dem_tiles'],
    extension = params['dem_extension'],
    tileset_path = paths['tileset_dem'],
    crs = params['crs']
)

# get intersection between mask and tileset
fct.vector_tools.ExtractBylocation(paths['tileset_landuse'], paths['mask'], paths['tileset_mask_landuse'], method = 'intersects')
fct.vector_tools.ExtractBylocation(paths['tileset_dem'], paths['mask'], paths['tileset_mask_dem'], method = 'intersects')
# probleme avec RGEALTI_FXX_0948_6457_MNT_LAMB93_IGN69.asc

# copy raster tiles
fct.raster_tools.ExtractRasterTilesFromTileset(
    tileset_path = paths['tileset_mask_landuse'],
    raster_dir = paths['inputs_dir_landuse_tiles'],
    dest_dir = paths['outputs_dir_landuse_tiles']
)

fct.raster_tools.ExtractRasterTilesFromTileset(
    tileset_path = paths['tileset_mask_dem'],
    raster_dir = paths['inputs_dir_dem_tiles'],
    dest_dir = paths['outputs_dir_dem_tiles']
)

# create virtual raster
bash_landuse = 'gdalbuildvrt -a_srs "EPSG:{}" "{}" "{}"*"{}"'.format(params['crs'], 
                                                                      paths['landuse_vrt'], 
                                                                      paths['outputs_dir_landuse_tiles'], 
                                                                      params['landuse_extension'])
fct.utils.process_with_stdout(bash_landuse)

bash_dem = 'gdalbuildvrt -a_srs "EPSG:{}" "{}" "{}"*"{}"'.format(params['crs'],
                                                                  paths['dem_vrt'], 
                                                                  paths['outputs_dir_dem_tiles'], 
                                                                  params['dem_extension'])
fct.utils.process_with_stdout(bash_dem)

# fit landuse pixels on dem
fct.raster_tools.fit_raster_pixel(raster_to_fit = paths['landuse_vrt'], 
                 reference_raster = paths['dem_vrt'],
                 output_raster = paths['landuse_fit'])

# create hydrologic network with strahler order 
fct.vector_tools.StrahlerOrder(hydro_network = paths['hydro_network'], 
                               output_network = paths['hydro_network_strahler'],
                               overwrite=True)

# Create networks sources
fct.vector_tools.CreateSources(hydro_network = paths['hydro_network'], 
                               output_sources = paths['sources'], 
                               overwrite=True)

### old process to extract from the whole France reference network, now the network must be prepared 
### on region and manually added in the input folder
# extract hydro network from mask with contains
# ExtractBylocation(paths['hydro_network'], paths['mask'], paths['hydro_network_mask'], method = 'contains')



