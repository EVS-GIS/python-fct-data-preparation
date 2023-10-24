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
from shapely.ops import unary_union
from rtree import index
from shapely.geometry import LineString, MultiLineString, mapping, Point
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