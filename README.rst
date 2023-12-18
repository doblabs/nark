@@@@
nark
@@@@

.. CXREF:
   https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/adding-a-workflow-status-badge

.. image:: https://github.com/doblabs/nark/actions/workflows/checks-unspecial.yml/badge.svg?branch=release
  :target: https://github.com/doblabs/nark/actions/workflows/checks-unspecial.yml/badge.svg?branch=release
  :alt: Build Status

.. CXREF: https://app.codecov.io/github.com/doblabs/nark/settings/badge

.. image:: https://codecov.io/gh/doblabs/nark/branch/release/graph/badge.svg?token=XXX
  :target: https://app.codecov.io/gh/doblabs/nark
  :alt: Coverage Status

.. image:: https://readthedocs.org/projects/nark/badge/?version=latest
  :target: https://nark.readthedocs.io/en/latest/
  :alt: Documentation Status

.. image:: https://img.shields.io/github/v/release/doblabs/nark.svg?style=flat
  :target: https://github.com/doblabs/nark/releases
  :alt: GitHub Release Status

.. image:: https://img.shields.io/pypi/v/nark.svg
  :target: https://pypi.org/project/nark/
  :alt: PyPI Release Status

.. image:: https://img.shields.io/pypi/pyversions/nark.svg
  :target: https://pypi.org/project/nark/
  :alt: PyPI Supported Python Versions

.. image:: https://img.shields.io/github/license/doblabs/nark.svg?style=flat
  :target: https://github.com/doblabs/nark/blob/release/LICENSE
  :alt: License Status

|

.. |dob| replace:: ``dob``
.. _dob: https://github.com/tallybark/dob

.. |dob-rtd| replace:: dob
.. _dob-rtd: https://dob.readthedocs.io/en/latest/

.. |dobbing| replace:: *dobbing*
.. _dobbing: https://dob.readthedocs.io/en/latest/usage.html

.. |nark| replace:: ``nark``
.. _nark: https://github.com/tallybark/nark

.. |hamster-lib| replace:: ``hamster-lib``
.. _hamster-lib: https://github.com/projecthamster/hamster-lib

.. |pip| replace:: ``pip``
.. _pip: https://pip.pypa.io/en/stable/

.. |Fact| replace:: *Fact*
.. _Fact: concepts.html

nark is a Python 3 support library for (at least one) journaling,
time tracking, and personal relationship management application(s).

nark provides an API for storing, retrieving, and reporting on time interval
data, aka timesheet or journal entries.

**NOTE:** You probably want to install a *client application*,
such as |dob-rtd|_ -- nark is usually installed automatically.

But if you want, you can install nark manually with |pip|_::

    pip install nark

For other setup options, read the
`installation guide <https://nark.readthedocs.io/en/latest/installation.html>`__.

#####
Story
#####

|nark|_ is inspired by
`Hamster <https://projecthamster.wordpress.com/>`__,
the esteemed time tracking application for
`GNOME <https://en.wikipedia.org/wiki/GNOME>`__.

|nark|_ is Hamster-friendly.
`Upgrade your existing database
<https://dob.readthedocs.io/en/latest/usage.html#upgrade-hamster>`__
and start |dobbing|_ today!

|nark|_ is a fork of the latent modern |hamster-lib|_ code rewrite.
The nark developers appreciate such a wonderful starting point!

|nark|_ is simply a |Fact|_ storage and reporting API, and does not
care about the database nor the user interface.
nark does one thing -- and only one thing -- and hopefully well!

|nark|_ is developed with the goal that any Python developer -- with
a few extra minutes and a sense of adventure -- would feel comfortable
banging on it when it breaks, or adding new features where they see a
need for improvement. (But hopefully you'll find that nark just works,
and that it already does what you want!)

########
Features
########

* Designed for modern Python releases (3.6, 3.7, and 3.8).
* Naturally Unicode compatible -- spice up your notes!
* Can migrate legacy Hamster databases (and fix integrity issues, too).
* Respectable coverage (to give you comfort knowing your Facts are safe).
* Decent documentation (including a live demo with inline instruction).
* Comfortable code base (focus on the feature, not on the format).
* Free and open source -- hack away!

See how you can
`contribute
<https://nark.readthedocs.io/en/latest/contributing.html>`__
to the project.

#######
Example
#######

This is a simple nark library usage example using the Python interpreter,
showing how to create a *Fact* instance from a *Factoid* string:

.. code-block:: Bash

    $ python3
    >>> from nark.items import Fact
    >>> factoid = '08:00 to 2019-02-16 10:00: act@cat: #tag1: Hello, nark!'
    >>> fact, err = Fact.create_from_factoid(factoid, time_hint='verify_both')
    >>> fact
    # Fact(
    #   pk=None,
    #   deleted=False,
    #   split_from=None,
    #   _start='08:00',
    #   _end=datetime.datetime(2019, 2, 16, 10, 0),
    #   _description='Hello, nark!',
    #   activity=Activity(
    #     pk=None
    #     deleted=False,
    #     _name='act',
    #     category=Category(
    #       pk=None,
    #       deleted=False,
    #       _name='cat',
    #     ),
    #   ),
    #   tags=[Tag(
    #     pk=None,
    #     deleted=False,
    #     _name='tag1',
    #   )],
    # )

.. image:: https://raw.githubusercontent.com/tallybark/nark/release/docs/_static/images/information-cat.png
   :target: https://nark.readthedocs.io/en/latest/authors.html#information-cat
   :align: center
   :alt: "Information Cat"

