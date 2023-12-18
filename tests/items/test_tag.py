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

from nark.items.tag import Tag


class TestTag(object):
    @classmethod
    def as_repr(cls, tag):
        if tag is None:
            return repr(tag)
        repred = (
            "Tag("
            "_name={name}, deleted={deleted}, freq={freq}, hidden={hidden}, pk={pk}"
            ")".format(
                pk=repr(tag.pk),
                name=repr(tag.name),
                deleted=repr(tag.deleted),
                freq=repr(tag.freq),
                hidden=repr(tag.hidden),
            )
        )
        return repred

    def test_init_valid(
        self, name_string_valid_parametrized_tag, pk_valid_parametrized
    ):
        """Make sure that Tag constructor accepts all valid values."""
        tag = Tag(name_string_valid_parametrized_tag, pk_valid_parametrized)
        assert tag.name == name_string_valid_parametrized_tag
        assert tag.pk == pk_valid_parametrized

    def test_init_invalid(self, name_string_invalid_parametrized_tag):
        """Make sure that Tag constructor rejects all invalid values."""
        with pytest.raises(ValueError):
            Tag(name_string_invalid_parametrized_tag)

    def test_as_tuple_include_pk(self, tag):
        """Make sure tags tuple representation works as intended and pk is included."""
        deleted = False
        hidden = False
        assert tag.as_tuple() == (tag.pk, tag.name, deleted, hidden)

    def test_as_tuple_exclude_pf(self, tag):
        """Make sure tags tuple representation works as intended and pk is excluded."""
        deleted = False
        hidden = False
        assert tag.as_tuple(include_pk=False) == (False, tag.name, deleted, hidden)

    def test_equal_fields_true(self, tag):
        """Make sure that two tags that differ only in their PK compare equal."""
        other_tag = copy.deepcopy(tag)
        other_tag.pk = 1
        assert tag.equal_fields(other_tag)

    def test_equal_fields_false(self, tag):
        """Make sure that two tags that differ not only in their PK compare unequal."""
        other_tag = copy.deepcopy(tag)
        other_tag.pk = 1
        other_tag.name += "foobar"
        assert tag.equal_fields(other_tag) is False

    def test__eq__false(self, tag):
        """Make sure that two distinct tags return ``False``."""
        other_tag = copy.deepcopy(tag)
        other_tag.pk = 1
        assert tag is not other_tag
        assert tag != other_tag

    def test__eq__true(self, tag):
        """Make sure that two identical categories return ``True``."""
        other_tag = copy.deepcopy(tag)
        assert tag is not other_tag
        assert tag == other_tag

    def test_is_hashable(self, tag):
        """Test that ``Tag`` instances are hashable."""
        assert hash(tag)

    def test_hash_method(self, tag):
        """Test that ``__hash__`` returns the hash expected."""
        assert hash(tag) == hash(tag.as_tuple())

    def test_hash_different_between_instances(self, tag_factory):
        """
        Test that different instances have different hashes.

        This is actually unneeded as we are merely testing the builtin ``hash``
        function and ``Tag.as_tuple`` but for reassurance we test it anyway.
        """
        assert hash(tag_factory()) != hash(tag_factory())

    def test__str__(self, tag):
        """Test string representation."""
        assert "{name}".format(name=tag.name) == str(tag)

    def test__repr__(self, tag):
        """Test representation method."""
        result = repr(tag)
        assert isinstance(result, str)
        expectation = TestTag.as_repr(tag)
        assert result == expectation
