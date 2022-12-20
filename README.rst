======
GoTime
======


.. image:: https://img.shields.io/pypi/v/gotime.svg
        :target: https://pypi.python.org/pypi/gotime
.. image:: https://img.shields.io/pypi/pyversions/gotime
        :alt: PyPI - Python Version
.. image:: https://img.shields.io/pypi/status/gotime
        :alt: PyPI - Status
.. image:: https://img.shields.io/pypi/dm/gotime
        :alt: PyPI - Downloads

.. image:: https://img.shields.io/travis/mgeiger/gotime.svg
        :target: https://travis-ci.org/mgeiger/gotime
.. image:: https://api.codeclimate.com/v1/badges/4ce6aa8b7e540fd923a2/maintainability
        :target: https://codeclimate.com/github/mgeiger/gotime/maintainability
        :alt: Maintainability
.. image:: https://readthedocs.org/projects/gotime/badge/?version=latest
        :target: https://gotime.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status
.. image:: https://pyup.io/repos/github/mgeiger/gotime/shield.svg
        :target: https://pyup.io/repos/github/mgeiger/gotime/
        :alt: Updates


How long does it take to get from Point A to Point B


* Free software: MIT license
* Documentation: https://gotime.readthedocs.io.


Features
--------

* Determine the time it takes to go from one address to a second address
* Works with a number of services included: Google Maps, Bing Maps, MapQuest
* Can be used as a command line call or via Python imports

Installation
------------

Package is hosted via warehouse in the PyPi repository.

You are able to install it via pip::

    pip install gotime

Usage
-----

Command Line
~~~~~~~~~~~~

After setting up your virtual environment, you can call by running::

    gotime --start="86 Brattle St., Cambridge, MA 02138" \
           --end="77 Massachusetts Ave., Cambridge, MA 02139"


Import
~~~~~~

Not properly implemented.


CI Setup
~~~~~~~~

.. mermaid::
    :alt: The image alternate text for HTML output
    :align: center
    :caption: Caption Text underneath the generated image

    sequenceDiagram
      participant Alice
      participant Bob
      Alice->John: Hello John, how are you?
      loop Healthcheck
          John->John: Fight against hypochondria
      end
      Note right of John: Rational thoughts <br/>prevail...
      John-->Alice: Great!
      John->Bob: How about you?



      Bob-->John: Jolly good!      


Credits
-------

A huge shoutout to mkazin_ for the project idea and the initial code.
Though most of the original code has been destroyed, the idea lives on.

.. _mkazin: https://github.com/mkazin

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
