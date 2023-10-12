# python-fct-data-preparation
Data preparation of the Python Fluvial Corridor Toolbox.

The FCT needs these data to work properly : 
- A DEM
- A raster landuse of the same resolution perfectly aligned with DEM
- The prepared hydrological network, see BDTOPO2REFHYDRO repository.
- The hydrological network source 

## Installation
In command line :

```
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