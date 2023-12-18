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


class TestAlchemyCategory(object):
    """Make sure our custom methods behave properly."""

    def test_as_hamster(self, alchemy_store, alchemy_category):
        """Make sure that conversion into a ``nark.Category```works as expected."""
        category = alchemy_category.as_hamster(alchemy_store)
        assert category.equal_fields(alchemy_category)


class TestAlchemyActivity(object):
    """Make sure our custom methods behave properly."""

    def test_as_hamster(self, alchemy_store, alchemy_activity):
        """Make sure that conversion into a ``nark.Activity```works as expected."""
        activity = alchemy_activity.as_hamster(alchemy_store)
        assert activity.equal_fields(alchemy_activity)

    def test_activity_has_facts(self, alchemy_store, alchemy_fact_factory):
        """Make sure that an activity can access ``Fact`` instances."""
        alchemy_fact = alchemy_fact_factory()
        assert alchemy_fact.activity
        activity = alchemy_fact.activity
        assert activity.facts


class TestAlchemyTag(object):
    """Make sure our custom methods behave properly."""

    def test_as_hamster(self, alchemy_store, alchemy_tag):
        """Make sure that conversion into a ``nark.Tag``works as expected."""
        tag = alchemy_tag.as_hamster(alchemy_store)
        assert tag.equal_fields(alchemy_tag)


class TestAlchemyFact(object):
    """Make sure our custom methods behave properly."""

    def test_adding_tags(self, alchemy_store, alchemy_fact, alchemy_tag):
        """
        Make sure that adding tags works as expected.

        This is closer to testing we got SQLAlchemy right than actual code.
        """
        assert len(alchemy_fact.tags) == 4
        alchemy_fact.tags.append(alchemy_tag)
        assert len(alchemy_fact.tags) == 5
        assert alchemy_tag in alchemy_fact.tags

    def test_setting_tags(self, alchemy_store, alchemy_fact, alchemy_tag_factory):
        """
        Make sure that adding tags works as expected.

        This is closer to testing we got SQLAlchemy right than actual code.
        """
        assert alchemy_fact.tags
        new_tags = [alchemy_tag_factory() for i in range(5)]
        alchemy_fact.tags = new_tags
        assert len(alchemy_fact.tags) == 5
        assert alchemy_fact.tags == new_tags

    def test_as_hamster(self, alchemy_store, alchemy_fact):
        """Make sure that conversion into a ``nark.Fact```works as expected."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        assert fact.equal_fields(alchemy_fact)
