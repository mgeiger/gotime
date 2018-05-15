#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `gotime` package."""
import os

import mock
import pytest

from click.testing import CliRunner

from gotime import gotime
from gotime import cli


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


def test_content(response):
    """Sample pytest test function with the pytest fixture as an argument."""
    # from bs4 import BeautifulSoup
    # assert 'GitHub' in BeautifulSoup(response.content).title.string


def test_command_line_interface():
    """Test the CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'gotime.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output


@mock.patch.dict(os.environ, {'GOOGLE_MAPS_API_KEY': 'FAKEKEY',
                              'BING_MAPS_API_KEY': 'FAKEKEY',
                              'MAPQUEST_API_KEY': 'FAKEKEY'})
def test_determine_keys_environmental_variables():
    map_keys = gotime.determine_keys()
    for map_key in map_keys:
        assert map_keys[map_key]
