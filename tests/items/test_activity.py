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

import copy

import pytest

from nark.items.activity import Activity

from .test_category import TestCategory


class TestActivity(object):
    @classmethod
    def as_repr(cls, activity):
        if activity is None:
            return repr(activity)
        repred = (
            "Activity(_name={name}, category={category}, "
            "deleted={deleted}, hidden={hidden}, pk={pk})"
        ).format(
            pk=repr(activity.pk),
            name=repr(activity.name),
            category=TestCategory.as_repr(activity.category),
            deleted=repr(activity.deleted),
            hidden=repr(activity.hidden),
        )
        return repred

    def test_init_valid(
        self,
        name_string_valid_parametrized,
        pk_valid_parametrized,
        category_valid_parametrized,
        deleted_valid_parametrized,
    ):
        """Test that init accepts all valid values."""
        activity = Activity(
            name_string_valid_parametrized,
            pk=pk_valid_parametrized,
            category=category_valid_parametrized,
            deleted=deleted_valid_parametrized,
        )
        assert activity.name == name_string_valid_parametrized
        assert activity.pk == pk_valid_parametrized
        assert activity.category == category_valid_parametrized
        assert activity.deleted == bool(deleted_valid_parametrized)

    def test_init_invalid(self, name_string_invalid_parametrized):
        """
        Test that init rejects all invalid values.

        Note:
            Right now, the only aspect that can have concievable invalid value
            is the name.
        """
        with pytest.raises(ValueError):
            Activity(name_string_invalid_parametrized)

    def test_create_from_composite(self, activity):
        result = Activity.create_from_composite(activity.name, activity.category.name)
        assert result.name == activity.name
        assert result.category == activity.category

    def test_as_tuple_include_pk(self, activity):
        """Make sure that conversion to a tuple matches our expectations."""
        expecting = (
            activity.pk,
            activity.name,
            (
                activity.category.pk,
                activity.category.name,
                activity.category.deleted,
                activity.category.hidden,
            ),
            activity.deleted,
            activity.hidden,
        )
        assert activity.as_tuple() == expecting

    def test_as_tuple_exclude_pk(self, activity):
        """Make sure that conversion to a tuple matches our expectations."""
        expecting = (
            False,
            activity.name,
            (
                False,
                activity.category.name,
                activity.category.deleted,
                activity.category.hidden,
            ),
            activity.deleted,
            activity.hidden,
        )
        assert activity.as_tuple(include_pk=False) == expecting

    def test_equal_fields_true(self, activity):
        """
        Make sure that two activities that differ only in their PK compare equal.
        """
        other = copy.deepcopy(activity)
        other.pk = 1
        assert activity.equal_fields(other)

    def test_equal_fields_false(self, activity):
        """
        Make sure that two activities that differ not only in their PK
        compare unequal.
        """
        other = copy.deepcopy(activity)
        other.pk = 1
        other.name += "foobar"
        assert activity.equal_fields(other) is False

    def test__eq__false(self, activity):
        """Make sure that two distinct activities return ``False``."""
        other = copy.deepcopy(activity)
        other.pk = 1
        assert activity is not other
        assert activity != other

    def test__eq__true(self, activity):
        """Make sure that two identical activities return ``True``."""
        other = copy.deepcopy(activity)
        assert activity is not other
        assert activity == other

    def test_is_hashable(self, activity):
        """Test that ``Category`` instances are hashable."""
        assert hash(activity)

    def test_hash_method(self, activity):
        """Test that ``__hash__`` returns the hash expected."""
        assert hash(activity) == hash(activity.as_tuple())

    def test_hash_different_between_instances(self, activity_factory):
        """
        Test that different instances have different hashes.

        This is actually unneeded as we are merely testing the builtin ``hash``
        function and ``Category.as_tuple`` but for reassurance we test it anyway.
        """
        assert hash(activity_factory()) != hash(activity_factory())

    def test__str__without_category(self, activity):
        activity.category = None
        assert str(activity) == "{name}".format(name=activity.name)

    def test__str__with_category(self, activity):
        assert str(activity) == "{name} ({category})".format(
            name=activity.name, category=activity.category.name
        )

    def test__repr__with_category(self, activity):
        """Make sure our debugging representation matches our expectations."""
        result = repr(activity)
        assert isinstance(result, str)
        expectation = TestActivity.as_repr(activity)
        assert result == expectation

    def test__repr__without_category(self, activity):
        """Make sure our debugging representation matches our expectations."""
        activity.category = None
        result = repr(activity)
        assert isinstance(result, str)
        expectation = TestActivity.as_repr(activity)
        assert result == expectation
