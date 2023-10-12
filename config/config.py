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

#!/usr/bin/python
from configparser import ConfigParser

def paths_config(filename='config/config.ini', section='paths'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section
    paths = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            paths[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return paths

def parameters_config(filename='config/config.ini', section='parameters'):
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section
    parameters = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            parameters[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return parameters
