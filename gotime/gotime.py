# -*- coding: utf-8 -*-

"""Main module."""
import os
from enum import Enum


class Keys(Enum):
    GOOGLE = 'GOOGLE_MAPS_API_KEY'
    BING = 'BING_MAPS_API_KEY'
    MAPQUEST = 'MAPQUEST_API_KEY'


class GoTime(object):

    def __init__(self, map_keys):
        self.map_keys = map_keys


def determine_keys():
    key_names = {'GOOGLE_MAPS_API_KEY': None,
                 'BING_MAPS_API_KEY': None,
                 'MAPQUEST_API_KEY': None}
    for key_name in key_names:
        key_names[key_name] = os.getenv(key_name)

    return key_names
