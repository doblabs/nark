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

import pytest


class TestTagManager:
    def test_save_new(self, basestore, tag, mocker):
        """Make sure that saving an new tag calls ``__add``."""
        mocker.patch.object(basestore.tags, "_add", return_value=tag)
        try:
            basestore.tags.save(tag)
        except NotImplementedError:
            pass
        assert basestore.tags._add.called

    def test_save_existing(self, basestore, tag, mocker):
        tag.pk = 0
        mocker.patch.object(basestore.tags, "_update", return_value=tag)
        try:
            basestore.tags.save(tag)
        except NotImplementedError:
            pass
        assert basestore.tags._update.called

    def test_save_wrong_type(self, basestore, tag):
        with pytest.raises(TypeError):
            basestore.tags.save([])

    def test_get_or_create_existing(self, basestore, tag, mocker):
        """Make sure the tag is beeing looked up and no new one is created."""
        mocker.patch.object(basestore.tags, "get_by_name", return_value=tag)
        mocker.patch.object(basestore.tags, "_add", return_value=tag)
        try:
            basestore.tags.get_or_create(tag.name)
        except NotImplementedError:
            pass
        assert basestore.tags._add.called is False
        assert basestore.tags.get_by_name.called

    def test_get_or_create_new_tag(self, basestore, tag, mocker):
        """Make sure the tag is beeing looked up and new one is created."""
        mocker.patch.object(basestore.tags, "_add", return_value=tag)
        mocker.patch.object(basestore.tags, "get_by_name", side_effect=KeyError)
        try:
            basestore.tags.get_or_create(tag.name)
        except NotImplementedError:
            pass
        assert basestore.tags.get_by_name.called
        assert basestore.tags._add.called

    def test_add_not_implemented(self, basestore, tag):
        with pytest.raises(NotImplementedError):
            basestore.tags._add(tag)

    def test_update_not_implemented(self, basestore, tag):
        with pytest.raises(NotImplementedError):
            basestore.tags._update(tag)

    def test_remove_not_implemented(self, basestore, tag):
        with pytest.raises(NotImplementedError):
            basestore.tags.remove(tag)

    def test_get_not_implemented_invalid_pk(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.tags.get(12)

    def test_get_not_implemented_invalid_pk_type(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.tags.get_by_name("fooo")

    def test_get_all_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.tags.get_all()

    def test_get_all_by_usage_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.tags.get_all_by_usage()

    def test_gather_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.tags.gather(query_terms=None)
