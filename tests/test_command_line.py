#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Tests for the GoTime Command Line Interface
"""
import pytest
from click.testing import CliRunner

from gotime import cli


@pytest.fixture(scope='module')
def runner():
    yield CliRunner()


@pytest.mark.usefixtures('runner')
def test_command_line_interface(runner):
    """Test the CLI."""
    runner = CliRunner()
    start = '1600 Pennsylvania Avenue, Washington DC'
    end = '11 Wall Street New York, NY'
    result = runner.invoke(cli.main, ['--start', start, '--end', end])
    assert result.exit_code == 0
    assert start in result.output and end in result.output


@pytest.mark.usefixtures('runner')
def test_command_line_help(runner):
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help' in help_result.output
    assert 'Show this message and exit.' in help_result.output
