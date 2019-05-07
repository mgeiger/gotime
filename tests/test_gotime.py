#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests for `gotime` package."""
import os

import mock
import pytest

from gotime.gotime import determine_keys, GoTime, Keys


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')
    pass


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string
    pass


@mock.patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'FAKEKEY',
                              'BING_MAPS_API_KEY': 'FAKEKEY',
                              'MAPQUEST_API_KEY': 'FAKEKEY'})
def test_determine_keys_environmental_variables():
    map_keys = determine_keys()
    for map_key in map_keys:
        assert map_keys[map_key], "{} not found in {}".format(map_key, map_keys)


# @pytest.mark.xfail(reason="Working on implementation.")
@mock.patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'FAKEKEY'})
def test_google_maps_failure():
    gt = GoTime(determine_keys())
    times = gt.get_times()
    print(times)
    print(Keys.GOOGLE)
    assert times[Keys.GOOGLE], "{} not found in {}".format(Keys.GOOGLE, times)

