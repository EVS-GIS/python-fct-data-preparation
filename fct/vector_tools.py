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
