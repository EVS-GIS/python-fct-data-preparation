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

import os
import click
import fiona
import fiona.crs
from shapely.geometry import shape, box
from shapely.ops import unary_union, nearest_points
from rtree import index
from shapely.geometry import LineString, MultiLineString, mapping, Point, MultiPoint
import numpy as np

def ExtractBylocation(input_file, mask_file, output_file, method):
    selected_features = []

    # Create spatial index for input layer
    input_index = index.Index()
    with fiona.open(input_file, 'r') as input_layer:
        for idx, input_feature in input_layer.items():
            in_feat = shape(input_feature['geometry'])
            input_index.insert(idx, in_feat.bounds)

    # Create spatial index for mask layer
    mask_index = index.Index()
    with fiona.open(mask_file, 'r') as mask_layer:
        for idx, mask_feature in mask_layer.items():
            mask_feat = shape(mask_feature['geometry'])
            mask_index.insert(idx, mask_feat.bounds)
    
    with fiona.open(mask_file, 'r') as mask_layer, fiona.open(input_file, 'r') as input_layer:
        options = dict(
                driver=input_layer.driver,
                schema=input_layer.schema.copy(),
                crs=input_layer.crs)

        for mask_feature in mask_layer:
            # print(polygon_feature)
            mask = shape(mask_feature['geometry'])

            # Get potential linestrings within the bounding box of the polygon
            potential_input = list(input_index.intersection(mask.bounds))

            for input_id  in potential_input:
                input_feature = input_layer[input_id]
                # print(linestring_feature)
                input = shape(input_feature['geometry'])

                if method == 'intersects':
                    if mask.intersects(input):
                        selected_features.append(input_feature)
                if method == 'contains':
                    if mask.contains(input):
                        selected_features.append(input_feature)
    # Create a new GeoPackage file and write the selected features to it
    with fiona.open(output_file, 'w', **options) as output_layer:
        for feature in selected_features:
            output_layer.write(feature)

def StrahlerOrder(hydro_network, output_network, overwrite=True):
    """
    Calculate Strahler stream order
    Parameters:
    - params (object): An object containing the parameters.
        - hydro_network (str): The filename of the hydro network.
        - hydrography_strahler (str): The filename for hydro network with Strahler order.
    - overwrite (bool): Optional. Specifies whether to overwrite existing tiled buffer files. Default is True.
    - source code from https://here.isnew.info/strahler-stream-order-in-python.html

    Returns:
    - None

    """
    click.secho('Compute Strahler order', fg='yellow')
    # file path definition
    # hydro_network = params.hydro_network.filename(tileset=tileset)
    # hydrography_strahler = params.hydrography_strahler.filename(tileset=tileset)

    # check overwrite
    if os.path.exists(output_network) and not overwrite:
        click.secho('Output already exists: %s' % output_network, fg='yellow')
        return

    # function to find head line in network (top upstream)
    def find_head_lines(lines):
        head_idx = []

        num_lines = len(lines)
        for i in range(num_lines):
            line = lines[i]
            first_point = line[0]

            has_upstream = False

            for j in range(num_lines):
                if j == i:
                    continue
                line = lines[j]
                last_point = line[len(line)-1]

                if first_point == last_point:
                    has_upstream = True

            if not has_upstream:
                head_idx.append(i)

        return head_idx

    # function to find next line downstream
    def find_next_line(curr_idx, lines):
        num_lines = len(lines)

        line = lines[curr_idx]
        last_point = line[len(line)-1]

        next_idx = None

        for i in range(num_lines):
            if i == curr_idx:
                continue
            line = lines[i]
            first_point = line[0]

            if last_point == first_point:
                next_idx = i
                break

        return next_idx

    # function to find sibling line (confluence line)
    def find_sibling_line(curr_idx, lines):
        num_lines = len(lines)

        line = lines[curr_idx]
        last_point = line[len(line)-1]

        sibling_idx = None

        for i in range(num_lines):
            if i == curr_idx:
                continue
            line = lines[i]
            last_point2 = line[len(line)-1]

            if last_point == last_point2:
                sibling_idx = i
                break

        return sibling_idx

    # read reference network
    with fiona.open(hydro_network, 'r') as source:

        schema = source.schema.copy()
        driver=source.driver
        crs=source.crs

        # define new fields
        strahler_field_name = "strahler"
        strahler_field_type = 'int'
        # Add the new field to the schema
        schema['properties'][strahler_field_name] = strahler_field_type

        lines = []
        source_copy = []

        # copy feature with strahler field in source_copy and the the line coordinates in lines
        for feature in source:
                # Create a new feature with the new field
                new_properties = feature['properties']
                new_properties[strahler_field_name] = 0  # Set the strahler field value to 0
                geom = shape(feature['geometry'])
                # copy line coordinates to find head line
                line = geom.coords
                lines.append(line)
                # copy features in new list to update the data before write all
                source_copy.append(feature)

        # save head lines index
        head_idx = find_head_lines(lines)

        with click.progressbar(head_idx) as processing:
            for idx in processing:
                curr_idx = idx
                curr_ord = 1
                # head lines order = 1
                source_copy[curr_idx]['properties'][strahler_field_name] = curr_ord
                # go downstream from each head lines
                while True:
                    # find next line downstream
                    next_idx = find_next_line(curr_idx, lines)
                    # stop iteration if no next line
                    if next_idx is None:
                        break
                    # copy next line feature and order
                    next_feat = source_copy[next_idx]
                    next_ord = next_feat['properties'][strahler_field_name]
                    # find sibling line
                    sibl_idx = find_sibling_line(curr_idx, lines)
                    # if confluence
                    if sibl_idx is not None:
                        sibl_feat = source_copy[sibl_idx]
                        sibl_ord = sibl_feat['properties'][strahler_field_name]
                        # check if confluence, and if same strahler order add +1 to order
                        if sibl_ord > curr_ord:
                            break
                        elif sibl_ord < curr_ord:
                            if next_ord == curr_ord:
                                break
                        else:
                            curr_ord += 1
                    # update order in next feature
                    source_copy[next_idx]['properties'][strahler_field_name] = curr_ord
                    # go further downstream
                    curr_idx = next_idx

                # write final features from updated features copy
                with fiona.open(output_network, 'w', driver=driver, crs=crs, schema=schema) as modif:
                    for feature in source_copy:
                        if feature['properties'][strahler_field_name] > 0:
                            modified_feature = {
                                    'type': 'Feature',
                                    'properties': feature['properties'],
                                    'geometry': feature['geometry'],
                                }

                            modif.write(modified_feature)

def CreateSources(hydro_network, output_sources, overwrite=True):
    """
    Create stream sources from reference hydrologic network : 

    Parameters:
    - params (object): An object containing the parameters for buffering.
        - hydrography_strahler_fieldbuf (str): The filename for hydro network pepared.
        - sources (str) : stream sources filename path output.
    - overwrite (bool): Optional. Specifies whether to overwrite existing tiled buffer files. Default is True.

    Returns:
    - None

    """
    click.secho('Create stream sources from hydrologic network', fg='yellow')
    # paths to files
    # hydrography_strahler_fieldbuf = params.hydrography_strahler_fieldbuf.filename(tileset=None)
    # sources = params.sources.filename(tileset=None)

    # check overwrite
    if os.path.exists(output_sources) and not overwrite:
        click.secho('Output already exists: %s' % output_sources, fg='yellow')
        return

    with fiona.open(hydro_network, 'r') as hydro:

        # Create output schema
        schema = hydro.schema.copy()
        schema['geometry'] = 'Point'

        options = dict(
            driver=hydro.driver,
            schema=schema,
            crs=hydro.crs)
        
        with fiona.open(output_sources, 'w', **options) as output:
            with click.progressbar(hydro) as processing:
            # extract network line with strahler = 1 and create point with first line point coordinates
                for feature in processing:
                    if feature['properties']['STRAHLER'] == 1:
                        properties = feature['properties']
                        geom = shape(feature['geometry'])
                        head_point = Point(geom.coords[0][:2])

                        output.write({
                            'geometry': mapping(head_point),
                            'properties': properties,
                        })

def IdentifyNetworkNodes(network, network_nodes, network_identified, crs):
    """
    Identifies network nodes by finding the endpoints of lines in a given network dataset and 
    quantizing their coordinates. The nodes are output as a separate dataset and their 
    attributes are added to the input network dataset. 
    
    Parameters
    ----------
    params : Parameters
        Input parameters.
    tileset : str, optional
        The tileset to use for the input and output datasets. Default is 'default'.
        
    Returns
    -------
    None
    
    Raises
    ------
    None
    """
    # Step 1
    click.secho('Get lines endpoints', fg='yellow')
    coordinates = list()
    
    def extract_coordinates(polyline):
        """ Extract endpoints coordinates
        """

        a = polyline['coordinates'][0]
        b = polyline['coordinates'][-1]
        coordinates.append(tuple(a))
        coordinates.append(tuple(b))
        
    with fiona.open(network) as fs:

        with click.progressbar(fs) as processing:
            for feature in processing:
                
                extract_coordinates(feature['geometry'])
                
        # Step 2
        click.secho('Quantize coordinates', fg='yellow')
        
        coordinates = np.array(coordinates)
        minx = np.min(coordinates[:, 0])
        miny = np.min(coordinates[:, 1])
        maxx = np.max(coordinates[:, 0])
        maxy = np.max(coordinates[:, 1])

        quantization = 1e8
        kx = (minx == maxx) and 1 or (maxx - minx)
        ky = (miny == maxy) and 1 or (maxy - miny)
        sx = kx / quantization
        sy = ky / quantization

        coordinates = np.int32(np.round((coordinates - (minx, miny)) / (sx, sy)))    
        
        # Step 3
        click.secho('Build endpoints index', fg='yellow')
        
        driver = 'GPKG'
        schema = {
            'geometry': 'Point',
            'properties': [
                ('GID', 'int')
            ]
        }
        crs = fiona.crs.CRS.from_epsg(crs)
        options = dict(driver=driver, crs=crs, schema=schema)
        
        with fiona.open(network_nodes, 'w', **options) as dst:
            
            coordinates_map = dict()
            gid = 0
            
            point_index = dict()
            
            with click.progressbar(enumerate(coordinates), length=len(coordinates)) as processing:
                for i, coordinate in processing:
                    
                    c = tuple(coordinate)
                    
                    if c not in coordinates_map:
                        
                        coordinates_map[c] = i
                        node_coords = (c[0]*sx + minx, c[1]*sy + miny)
                         
                        point_index[gid] = Point(node_coords[0], node_coords[1])
                        
                        dst.write({
                            'type': 'Feature',
                            'geometry': {'type': 'Point', 'coordinates': node_coords},
                            'properties': {'GID': gid}
                        }) 

                        gid = gid + 1

            del coordinates
            del coordinates_map
            
        # Step 4
        click.secho('Output lines with nodes attributes', fg='yellow')
        
        nodes_list = MultiPoint(list(point_index.values()))

        def nearest(point):
            """ Return the nearest point in the point index
            """
            nearest_node = nearest_points(point, nodes_list)[1]
            
            for candidate in point_index:
                if point_index[candidate].equals(nearest_node):
                    return candidate
                
            return None

        schema = fs.schema
        schema['properties']['NODEA'] = 'int:10'
        schema['properties']['NODEB'] = 'int:10'

        options = dict(driver=driver, crs=crs, schema=schema)

        with fiona.open(network_identified, 'w', **options) as dst:
            with click.progressbar(fs) as processing:
                for feature in processing:
                    
                    output_feature = feature
                    
                    a = Point(output_feature['geometry']['coordinates'][0])
                    b = Point(output_feature['geometry']['coordinates'][-1])
                    
                    output_feature['properties']['NODEA'] = nearest(a)
                    output_feature['properties']['NODEB'] = nearest(b)
                    
                    dst.write(output_feature)

def prepare_network_attribut(network_file, output_file, crs):
    """
    Prepare network attributes and create a new output file with additional fields.

    Parameters:
    - network_file (str): Path to the input network file.
    - output_file (str): Path to the output file where the modified network will be saved.
    - crs (dict): Coordinate Reference System information to be used for the output file.

    Returns:
    None

    Opens the specified network file, adds new fields (CDENTITEHY, AXIS, TOPONYME) to the schema,
    and creates a new output file with the modified schema and additional fields.

    The new fields are populated based on existing properties in the input network file.

    Raises:
    IOError: If there is an issue opening or processing the network file.
    ValueError: If there is an issue with the provided Coordinate Reference System.
    """

    fields_to_remove = ['date_creation', 'date_modification', 'date_d_apparition', 'date_de_confirmation']

    # open network file
    with fiona.open(network_file) as source:
        schema = {
            'geometry': source.schema['geometry'],
            'properties': {k: v for k, v in source.schema['properties'].items() if k not in fields_to_remove}
        }
        driver=source.driver
        crs=source.crs

        # define the new fields
        cdentitehy_field_name = "CDENTITEHY"
        cdentitehy_field_type = 'str'
        axis_field_name = "AXIS"
        axis_field_type = 'int'
        toponyme_field_name = "TOPONYME"
        toponyme_field_type = 'str'

        # Add the new fields to the schema
        schema['properties'][cdentitehy_field_name] = cdentitehy_field_type
        schema['properties'][axis_field_name] = axis_field_type
        schema['properties'][toponyme_field_name] = toponyme_field_type

        # open output file in write mode
        with fiona.open(output_file, 'w', driver=driver, crs=crs, schema=schema) as output:

            # create progressbar during processing
            with click.progressbar(source) as processing:
                for feature in processing:

                    properties = {k: v for k, v in feature['properties'].items() if k not in fields_to_remove}

                    # update features new fields
                    properties[cdentitehy_field_name] = properties['code_du_cours_d_eau_bdcarthage']
                    liens_vers_cours_d_eau = properties['liens_vers_cours_d_eau']
                    properties[axis_field_name] = int(liens_vers_cours_d_eau[8:])
                    properties[toponyme_field_name] = properties['cpx_toponyme_de_cours_d_eau']

                    # create the feature to copy in output file
                    new_feature = {
                                            'type': 'Feature',
                                            'properties': properties,
                                            'geometry': feature['geometry'],
                                        }

                    # write feature in output file
                    output.write(new_feature)

    print(cdentitehy_field_name + ', ' + axis_field_name + ' and ' + toponyme_field_name + ' fields adds and populate to ' + output_file)

