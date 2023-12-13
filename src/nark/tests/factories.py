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

"""Factories which generate ready-to-use, randomized nark class object instances."""

import datetime

# BEWARE: This module imports packages that are installed for developers only,
# via requirements/test.pip, and are not specified as package dependencies. So do
# not load from this module from any nark-proper code! Normal users are not to be
# expected to have these libraries available. Only load this module from other tests.

import factory
import fauxfactory

from nark.items.activity import Activity
from nark.items.category import Category
from nark.items.fact import Fact
from nark.items.tag import Tag


# 2020-01-30: (lb): DRYing time: Here's a little history, because I made some
# assumptions when I merged the two, not-so-DRY, factories.py from nark and dob.
# - There were two sources of divergence:
#   - hamster-lib's factories.py used factory.Faker(), instead of faker(),
#     for Fact.start.
#   - hamster-lib's factories.py used factory.LazyAttribute and fauxfactory
#     to generate Category.name, instead of factory.Faker.
# - I think hamster-lib had the most up to date code -- the original behavior
#   was committed 2015-12-17 to hamster-lib, and later copied to hamster-cli.
#   Then, changes were made to the factories.py module in hamster-lib, but not
#   to the copy-pasta version in hamster-cli. From hamster-lib's log:
#       2016-06-24 hamster-lib elbenfreund c84f189a
#       This removes the naive and error prone usage of stand alone ``faker``
#       calls in our factories for the proper ``factory.Faker`` ones. Those
#       basicly wrap our calls in ``LazyAttributes``. Where we generate random
#       data from non-faker sources, e.g. ``fauxfactory`` we make sure to do the
#       wrapping ourselfs.
#   I don't quite understand what the issue was, but sounds like the
#   solution is to not use faker() (from `import faker`), but to use
#   factory.Faker() (and also factory.LazyAttribute with fauxfactory).

class CategoryFactory(factory.Factory):
    """Test fixture factory returns new ``Category`` with random attribute values."""

    pk = None
    # 2020-01-30: (lb): DRYing time: I consolidated factories.py from nark and dob
    # and saw this code from dob (which came from hamster-cli, which was copied from
    # hamster-lib; but the hamster-cli copy is missing a bugfix that hamster-lib's
    # copy received; here's the original code):
    #
    #   name = factory.Faker('word')
    #
    # Here's a comment from elbenfreund, from tests/hamster_lib/factories.py,
    # regarding the newer use of LazyAttribute:
    #
    #   # Although we do not need to reference to the object beeing created and
    #   # ``LazyFunction`` seems sufficient it is not as we could not pass on the
    #   # string encoding. ``LazyAttribute`` allows us to specify a lambda that
    #   # circumvents this problem.
    name = factory.LazyAttribute(lambda x: fauxfactory.gen_string('utf8'))

    class Meta:
        model = Category


class ActivityFactory(factory.Factory):
    """Test fixture factory returns new ``Activity`` with random attribute values."""

    pk = None
    name = factory.Faker('word')
    category = factory.SubFactory(CategoryFactory)
    deleted = False

    class Meta:
        model = Activity


class TagFactory(factory.Factory):
    """Test fixture factory returns new ``Tag`` with random attribute values."""

    pk = None
    name = factory.Faker('word')

    class Meta:
        model = Tag


class FactFactory(factory.Factory):
    """Test fixture factory returns new ``Fact`` with random attribute values.

    Each new instance has a three-hour duration (i.e., the start time is
    randomized, and the end time is calculated three hours after that).
    """

    pk = None
    activity = factory.SubFactory(ActivityFactory)

    # 2020-01-30: (lb): DRYing time: I consolidated factories.py from nark and dob,
    # and here's the second discrepancy I found (where I think hamster-cli was
    # overlooked by a bugfix applied to hamster-lib). The original code was committed
    # way back when and used faker:
    #   # 2015-12-17 hamster-lib tests/factories.py 52976ac0
    #   import faker
    #   start = faker.Faker().date_time()
    #   end = start + datetime.timedelta(hours=3)
    # and then hamster-lib (but not the -cli) was updated 2016-06-24 (c84f189a) thusly:
    start = factory.Faker('date_time')
    end = factory.LazyAttribute(lambda o: o.start + datetime.timedelta(hours=3))
    description = factory.Faker('paragraph')

    class Meta:
        model = Fact

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add new random tags after instance creation."""
        self.tags = set([TagFactory() for i in range(1)])

