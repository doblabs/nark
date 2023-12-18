# This file exists within 'nark':
#
#   https://github.com/tallybark/nark
#
# Copyright © 2018-2020 Landon Bouma. All rights reserved.
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

"""Tests for nark.backends.sqlalchemy.managers.gather_base.GatherBaseAlchemyManager."""

import pytest

from nark.backends.sqlalchemy.managers.gather_base import GatherBaseAlchemyManager
from nark.backends.sqlalchemy.objects import AlchemyActivity
from nark.managers.query_terms import QueryTerms
from nark.items.activity import Activity


# (lb): You'll find much of GatherBaseAlchemyManager tested by derived classes' tests.
# What's not tested by one of the derived classes should be covered here, albeit often
# we use the Activity as the search class.


class TestGatherBaseAlchemyManager:
    """"""

    # MAYBE: Move five_report_facts_ctl from dob to nark, which is a session-scoped
    # five-Facts fixture, which can noticeably speed up tests. For now, use the
    # simpler set_of_alchemy_facts which isn't the quickest fixture, but we can
    # just not perform these tests for the other item types (category and tag)
    # because the code under test here is not item-specific.

    def test_get_all_count_results(self, alchemy_store, set_of_alchemy_facts):
        count = alchemy_store.activities.get_all(count_results=True)
        assert count == len(set_of_alchemy_facts)

    def test_get_all_no_query_terms_raw(self, alchemy_store, set_of_alchemy_facts):
        """Test query_process_results._process_records_items_only second branch."""
        results = alchemy_store.activities.get_all(raw=True)
        # Each fixture Fact was assigned a unique Activity.
        assert len(results) == len(set_of_alchemy_facts)
        # Each result is a raw AlchemyActivity.
        assert isinstance(results[0], AlchemyActivity)

    def test_get_all_include_stats_act(self, alchemy_store, set_of_alchemy_facts):
        results = alchemy_store.activities.get_all(include_stats=True)
        # Each fixture Fact was assigned a unique Activity.
        assert len(results) == len(set_of_alchemy_facts)
        activity, uses, duration = results[0]
        # Each result's first item is a hydrated Activity.
        assert isinstance(activity, Activity)
        # Because all fixture Activity names are unique, only 1 use of it.
        assert uses == 1

    def test_get_all_include_stats_raw(self, alchemy_store, set_of_alchemy_facts):
        """Test query_process_results._process_records_items_and_aggs second branch."""
        results = alchemy_store.activities.get_all(include_stats=True, raw=True)
        # Each fixture Fact was assigned a unique Activity.
        assert len(results) == len(set_of_alchemy_facts)
        activity, uses, duration = results[0]
        # Each result's first item is a raw AlchemyActivity.
        assert isinstance(activity, AlchemyActivity)
        # Because all fixture Activity names are unique, only 1 use of it.
        assert uses == 1

    def test_get_all_include_stats_not_implemented(self, alchemy_store, mocker):
        """Test that unimplemented _gather_query_start_aggregate raises."""
        unclassed = GatherBaseAlchemyManager()
        unclassed._gather_query_alchemy_cls = mocker.MagicMock()
        unclassed.store = mocker.MagicMock()
        mocker.patch.object(unclassed, "_gather_query_alchemy_cls")
        qt = QueryTerms(include_stats=True)
        # Test _gather_query_start_aggregate raises.
        with pytest.raises(NotImplementedError):
            unclassed.gather(qt)

    def test_get_all_compute_stats_exclude(self, alchemy_store, set_of_alchemy_facts):
        """Test query_process_results._process_records_items_and_aggs_hydrate branch."""
        results = alchemy_store.activities.get_all(sort_cols=["usage"])
        # Each fixture Fact was assigned a unique Activity.
        assert len(results) == len(set_of_alchemy_facts)
        # Each result is a hydrated Activity.
        assert isinstance(results[0], Activity)

    def test_get_all_fact_without_activity(self, alchemy_store, alchemy_fact):
        """Test query_process_results._as_hamster_or_none second branch."""
        alchemy_fact.activity = None
        results = alchemy_store.activities.get_all(include_stats=True)
        activity, uses, duration = results[0]
        assert activity is None
        assert uses == 1

    def test_get_all_endless_true(self, alchemy_store, set_of_alchemy_facts_active):
        results = alchemy_store.activities.get_all(endless=True)
        # Only 1 Fact is endless.
        assert len(results) == 1

    def test_get_all_query_prepared_trace(self, alchemy_store, mocker):
        alchemy_store.config["dev.catch_errors"] = True
        mocker.patch.object(alchemy_store.logger, "warning")
        alchemy_store.activities.get_all()
        assert alchemy_store.logger.warning.called
