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

"""Basic item class object generators."""

from pytest_factoryboy import register

from nark.tests import factories

# NOTE: To make the factories available to a test, import this file
#       from the test module or from a conftest along its path.
#       - You'll want to glob everything to get fact_factory, etc. E.g.,
#         Use this style import:
#           # Register the fact_factory, etc.
#           from nark.tests.item_factories import *  # noqa: F401, F403

# For generating backend store items, see the Alchemy item generators:
#
#   nark/tests/backends/sqlalchemy/conftest.py

register(factories.CategoryFactory)
register(factories.ActivityFactory)
register(factories.TagFactory)
register(factories.FactFactory)

# Note that registering the FactFactory, for example, is essentially:
#
#   @pytest.fixture
#   def fact_factory():
#       """Return a factory class that generates non-persisting Fact instances."""
#       return factories.FactFactory.build

