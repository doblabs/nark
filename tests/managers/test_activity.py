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


class TestActivityManager:
    def test_save_new(self, basestore, activity, mocker):
        """Make sure that saving an new activity calls ``_add``."""
        mocker.patch.object(basestore.activities, "_add", return_value=activity)
        try:
            basestore.activities.save(activity)
        except NotImplementedError:
            pass
        assert basestore.activities._add.called

    def test_save_existing(self, basestore, activity, mocker):
        """Make sure that saving an existing activity calls ``_update``."""
        activity.pk = 0
        mocker.patch.object(basestore.activities, "_update", return_value=activity)
        try:
            basestore.activities.save(activity)
        except NotImplementedError:
            pass
        assert basestore.activities._update.called

    def test_get_or_create_existing(self, basestore, activity, mocker):
        mocker.patch.object(
            basestore.activities,
            "get_by_composite",
            return_value=activity,
        )
        mocker.patch.object(basestore.activities, "save", return_value=activity)
        result = basestore.activities.get_or_create(activity)
        assert result.name == activity.name
        assert basestore.activities.save.called is False

    def test_get_or_create_new(self, basestore, activity, mocker):
        mocker.patch.object(
            basestore.activities,
            "get_by_composite",
            side_effect=KeyError(),
        )
        mocker.patch.object(basestore.activities, "save", return_value=activity)
        result = basestore.activities.get_or_create(activity)
        assert result.name == activity.name
        assert basestore.activities.save.called is True

    def test_add_not_implemented(self, basestore, activity):
        with pytest.raises(NotImplementedError):
            basestore.activities._add(activity)

    def test_update_not_implemented(self, basestore, activity):
        with pytest.raises(NotImplementedError):
            basestore.activities._update(activity)

    def test_remove_not_implemented(self, basestore, activity):
        with pytest.raises(NotImplementedError):
            basestore.activities.remove(activity)

    def test_get_by_composite_not_implemented(self, basestore, activity):
        with pytest.raises(NotImplementedError):
            basestore.activities.get_by_composite(activity.name, activity.category)

    def test_get_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.activities.get(12)

    def test_get_all_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.activities.get_all()

    def test_get_all_by_usage_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.activities.get_all_by_usage()

    def test_gather_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.activities.gather(query_terms=None)
