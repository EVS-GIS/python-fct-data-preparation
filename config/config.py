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
