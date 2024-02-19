# python-fct-data-preparation
Data preparation of the Python Fluvial Corridor Toolbox.

The FCT need some dataset to work properly : 
- A DEM.
- A raster landuse with the cells fitted on the DEM ones and the same resolution.
- A hydrological network matching the landuse with checked topology linestrings, without multichannels, .
- The rivers sources matching the hydrological network with the same fields.

This program prepare these datasets. All the data must a fit the spatial footprint of the territory the FCT will run. A mask vector geopackage with a single polygon contains the watershed to compute. The DEM and the landuse data should be organise by tiles, each ones need to be in a single folder.
The hydrological network should be from the IGN BDTOO database, see [BDTOPO2REFHYDRO](https://github.com/EVS-GIS/bdtopo2refhydro) repository. Landuse tiles are from [landuse-fct](https://github.com/EVS-GIS/landuse-fct) repository.

prepare_fct_data_workflow.py prepares the dataset as follows: 
- Set the parameters and file paths from the config.ini file.
- Create dem and landuse tileset from the tiles directories. For each dataset, a tileset geopackage file is created with all the tiles inside the directory.
- The intersection between the mask and these tilesets identify in new geopackage the tiles to keep.
- These tilesets with the tiles to keep is used to copy the tiles from the main tiles directory.
- Virtual rasters are created from these tiles.
- The landuse raster cells are fitted to DEM ones.
- Some specific fields are created to the hydrological network (CDENTITEHY, AXIS, TOPONYME), the date fields are remove (not supported by ESRI shapefile).
- The sources are create based on the Strahler rank 1 streams with all the attributs from the hydrological network.

## Installation
In command line :

``` bash
# go to the working folder you want to download the mapdo application
cd Path/to/my/folder
# copy mapdo repository with git
git clone https://github.com/EVS-GIS/python-fct-data-preparation.git
# go to gis_python_tools folder
cd python-fct-data-preparation
# create a new virtual environnement in python 3
python3 -m venv env --prompt python-fct-data-preparation
# activate your new environment
.\env\Scripts\activate
# update pip
python3 -m pip install -U pip
# install package in environment
pip install -r requirements.txt
# create a config.ini file in config folder
```

An configuration exemple is in config/config_example.ini. Rename it to config.ini to use it.

## How to cite

Manière, L. (2024). python-fct-data-preparation (Version 1.0.0) [Computer software]. https://github.com/EVS-GIS/python-fct-data-preparation

## Licence

This program is released under the [GNU Public License v3](https://github.com/EVS-GIS/python-fct-data-preparation/blob/main/LICENSE).