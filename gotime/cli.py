# -*- coding: utf-8 -*-

"""Console script for gotime."""
import os
import sys

import click

from gotime import GoTime, Keys


@click.command()
@click.option('--start', help="The start location")
@click.option('--end', help="The end location")
def main(start, end):
    """
    Give me a start location and an end location and
    I will determine how long it will take to get there.

    I will be looking for environmental variables using 
    the following format:

    `<SERVICE>_API_KEY`

    Where <SERVICE> can be any of the following:
    
    * GOOGLE_MAPS\n
    * BING_MAPS\n
    * MAPQUEST

    """
    print(f"Going from {start} to {end}")

    
    key_list = list()
    for key in Keys:
        key_list = (key.name, os.getenv(key.value, None))

    gt = GoTime(key_list)

    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
