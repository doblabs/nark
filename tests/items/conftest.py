# This file exists within 'nark':
#
#   https://github.com/tallybark/nark
#
# Copyright © 2018-2020 Landon Bouma
# Copyright © 2015-2016 Eric Goller
# All  rights  reserved.
#
# 'nark' is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License  as  published by the Free Software Foundation,
# either version 3  of the License,  or  (at your option)  any   later    version.
#
# 'nark' is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY  or  FITNESS FOR A PARTICULAR
# PURPOSE.  See  the  GNU General Public License  for  more details.
#
# You can find the GNU General Public License reprinted in the file titled 'LICENSE',
# or visit <http://www.gnu.org/licenses/>.

"""Fixtures that are of general use."""

import datetime

import pytest

from nark.tests import factories

# Register the category_factory, etc.
from nark.tests.item_factories import *  # noqa: F401, F403

# ***

# Fixtures for: tests/items/test_activity.py.


# Categories
@pytest.fixture(
    params=(
        None,
        True,
    )
)
def category_valid_parametrized(
    request,
    category_factory,
    name_string_valid_parametrized,
):
    """Provide a variety of valid category fixtures."""
    if request.param:
        result = category_factory(name=name_string_valid_parametrized)
    else:
        result = None
    return result


# +++

# (lb): Unused.


@pytest.fixture
def category_valid_parametrized_without_none(
    request,
    category_factory,
    name_string_valid_parametrized,
):
    """
    Provide a parametrized category fixture but not ``None``.

    This fixuture will represent a wide array of potential name charsets as well
    but not ``category=None``.
    """
    return category_factory(name=name_string_valid_parametrized)


# Activities
@pytest.fixture
def activity_valid_parametrized(
    request,
    activity_factory,
    name_string_valid_parametrized,
    category_valid_parametrized,
    deleted_valid_parametrized,
):
    """Provide a huge array of possible activity versions. Including None."""
    return activity_factory(
        name=name_string_valid_parametrized,
        category=category_valid_parametrized,
        deleted=deleted_valid_parametrized,
    )


@pytest.fixture
def new_activity_values(category):
    """Return garanteed modified values for a given activity."""

    def modify(activity):
        return {
            "name": activity.name + "foobar",
        }

    return modify


# ***

# Fixtures for: tests/items/test_fact.py.


@pytest.fixture
def fact():
    """Provide a randomized non-persistant Fact-instance."""
    return factories.FactFactory.build()


# +++


@pytest.fixture(params=("%M", "%H:%M", "HHhMMm", ""))
def string_delta_style_parametrized(request):
    """Provide all possible format option for ``Fact().format_delta()``."""
    return request.param


# ***

# (lb): Unused.


@pytest.fixture
def today_fact(fact_factory):
    """Return a ``Fact`` instance that start and ends 'today'."""
    # MAYBE: Use controller.store.now ?
    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(minutes=30)
    return fact_factory(start=start, end=end)


@pytest.fixture
def not_today_fact(fact_factory):
    """Return a ``Fact`` instance that neither start nor ends 'today'."""
    # MAYBE: Use controller.store.now ?
    start = datetime.datetime.utcnow() - datetime.timedelta(days=2)
    end = start + datetime.timedelta(minutes=30)
    return fact_factory(start=start, end=end)


@pytest.fixture
def current_fact(fact_factory):
    """Provide a ``ongoing fact``, which has a start time but no end time."""
    # MAYBE: Use controller.store.now ?
    return fact_factory(
        start=datetime.datetime.utcnow().replace(microsecond=0),
        end=None,
    )
