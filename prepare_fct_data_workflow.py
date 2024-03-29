#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
-------------------------------------------------------------------------------
"This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
-------------------------------------------------------------------------------
"""

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
# RGEALTI_FXX_0948_6457_MNT_LAMB93_IGN69.asc manquant lorsque lancement de l'Isère seule, pas de problème visible pour RMC.

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

# create a text file with the list of the dem file for long list to avoid error argument list too long
dem_masked_files = 'find {} -name "*{}" > {}'.format(paths['outputs_dir_dem_tiles'],
                                                               params['dem_extension'],
                                                               paths['dem_masked_files'])

fct.utils.process_with_stdout(dem_masked_files)

bash_dem = 'gdalbuildvrt -a_srs EPSG:{} -input_file_list {} {}'.format(
                                                                  params['crs'],
                                                                  paths['dem_masked_files'],
                                                                  paths['dem_vrt'])

fct.utils.process_with_stdout(bash_dem)

# fit landuse pixels on dem
fct.raster_tools.fit_raster_pixel(raster_to_fit = paths['landuse_vrt'], 
                 reference_raster = paths['dem_vrt'],
                 output_raster = paths['landuse_fit'])

# Prepare the attibut table to the Fluvial Corridor Toolbox needs
fct.vector_tools.prepare_network_attribut(network_file = paths['hydro_network'], 
                                          output_file = paths['hydro_network_output'],
                                          crs = params['crs'])

# Create networks sources
fct.vector_tools.CreateSources(hydro_network = paths['hydro_network_output'], 
                               output_sources = paths['sources'], 
                               overwrite=True)
