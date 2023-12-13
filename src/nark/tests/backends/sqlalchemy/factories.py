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

"""Factories for sqlalchemy models."""

import datetime

import factory
import faker
from nark.backends.sqlalchemy.objects import (
    AlchemyActivity,
    AlchemyCategory,
    AlchemyFact,
    AlchemyTag
)

from . import common


class AlchemyCategoryFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory class for generic ``AlchemyCategory`` instances."""

    # (lb): factoryboy starts step.sequence at 0,
    #   and we want positive PKs, so add one.
    pk = factory.Sequence(lambda n: n + 1)

    @factory.sequence
    def name(n):  # NOQA
        """Return a name that is guaranteed to be unique."""
        return '{name} - {key}'.format(name=faker.Faker().word(), key=n)

    deleted = False
    hidden = False

    class Meta:
        model = AlchemyCategory
        sqlalchemy_session = common.Session
        sqlalchemy_session_persistence = 'flush'


class AlchemyActivityFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory class for generic ``AlchemyActivity`` instances."""

    pk = factory.Sequence(lambda n: n + 1)
    name = factory.Faker('sentence')
    category = factory.SubFactory(AlchemyCategoryFactory)
    deleted = False
    hidden = False

    class Meta:
        model = AlchemyActivity
        sqlalchemy_session = common.Session
        sqlalchemy_session_persistence = 'flush'


class AlchemyTagFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory class for generic ``AlchemyTag`` instances."""

    pk = factory.Sequence(lambda n: n + 1)

    @factory.sequence
    def name(n):  # NOQA
        """Return a name that is guaranteed to be unique."""
        return '{name} - {key}'.format(name=faker.Faker().word(), key=n)

    deleted = False
    hidden = False
    # Skip `freq`, which is not part of the Tag table.

    class Meta:
        model = AlchemyTag
        sqlalchemy_session = common.Session
        sqlalchemy_session_persistence = 'flush'


class AlchemyFactFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory class for generic ``AlchemyFact`` instances."""

    pk = factory.Sequence(lambda n: n + 1)
    activity = factory.SubFactory(AlchemyActivityFactory)
    start = factory.Faker('date_time')
    end = factory.LazyAttribute(lambda o: o.start + datetime.timedelta(hours=3))
    description = factory.Faker('paragraph')

    class Meta:
        model = AlchemyFact
        sqlalchemy_session = common.Session
        sqlalchemy_session_persistence = 'flush'

    deleted = False
    split_from = None

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        """Add new random tags after instance creation."""
        self.tags = list([AlchemyTagFactory() for i in range(4)])

