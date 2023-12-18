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

from nark.items.category import Category


class TestCategory(object):
    @classmethod
    def as_repr(cls, category):
        if category is None:
            return repr(category)
        repr_f = "Category(_name={name}, deleted={deleted}, hidden={hidden}, pk={pk})"
        repred = repr_f.format(
            pk=repr(category.pk),
            name=repr(category.name),
            deleted=repr(category.deleted),
            hidden=repr(category.hidden),
        )
        return repred

    def test_init_valid(self, name_string_valid_parametrized, pk_valid_parametrized):
        """Make sure that Category constructor accepts all valid values."""
        category = Category(name_string_valid_parametrized, pk_valid_parametrized)
        assert category.name == name_string_valid_parametrized
        assert category.pk == pk_valid_parametrized

    def test_init_invalid(self, name_string_invalid_parametrized):
        """Make sure that Category constructor rejects all invalid values."""
        with pytest.raises(ValueError):
            Category(name_string_invalid_parametrized)

    def test_as_tuple_include_pk(self, category):
        """
        Make sure categories tuple representation works as intended and pk
        is included.
        """
        deleted = False
        hidden = False
        assert category.as_tuple() == (category.pk, category.name, deleted, hidden)

    def test_as_tuple_exclude_pf(self, category):
        """
        Make sure categories tuple representation works as intended and pk
        is excluded.
        """
        deleted = False
        hidden = False
        cat_tuple = category.as_tuple(include_pk=False)
        our_tuple = (False, category.name, deleted, hidden)
        assert cat_tuple == our_tuple

    def test_equal_fields_true(self, category):
        """
        Make sure that two categories that differ only in their PK compare equal.
        """
        other_category = copy.deepcopy(category)
        other_category.pk = 1
        assert category.equal_fields(other_category)

    def test_equal_fields_false(self, category):
        """
        Make sure that two categories that differ not only in their PK
        compare unequal.
        """
        other_category = copy.deepcopy(category)
        other_category.pk = 1
        other_category.name += "foobar"
        assert category.equal_fields(other_category) is False

    def test__eq__false(self, category):
        """Make sure that two distinct categories return ``False``."""
        other_category = copy.deepcopy(category)
        other_category.pk = 1
        assert category is not other_category
        assert category != other_category

    def test__eq__true(self, category):
        """Make sure that two identical categories return ``True``."""
        other_category = copy.deepcopy(category)
        assert category is not other_category
        assert category == other_category

    def test_is_hashable(self, category):
        """Test that ``Category`` instances are hashable."""
        assert hash(category)

    def test_hash_method(self, category):
        """Test that ``__hash__`` returns the hash expected."""
        assert hash(category) == hash(category.as_tuple())

    def test_hash_different_between_instances(self, category_factory):
        """
        Test that different instances have different hashes.

        This is actually unneeded as we are merely testing the builtin ``hash``
        function and ``Category.as_tuple`` but for reassurance we test it anyway.
        """
        assert hash(category_factory()) != hash(category_factory())

    def test__str__(self, category):
        """Test string representation."""
        assert "{name}".format(name=category.name) == str(category)

    def test__repr__(self, category):
        """Test representation method."""
        result = repr(category)
        assert isinstance(result, str)
        expectation = TestCategory.as_repr(category)
        assert result == expectation
