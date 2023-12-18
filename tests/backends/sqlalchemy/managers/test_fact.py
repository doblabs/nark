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

import datetime

import pytest
from freezegun import freeze_time

from nark.backends.sqlalchemy.objects import AlchemyActivity, AlchemyFact, AlchemyTag


class TestFactManager:
    """"""

    def test_add_fails_timeframe_available_existing_fact_overlaps_start_only(
        self,
        alchemy_store,
        fact,
        alchemy_fact,
    ):
        """
        Make sure that passing a fact with only start overlapping an existing
        one raises error.
        """
        fact.start = alchemy_fact.start - datetime.timedelta(days=4)
        fact.end = alchemy_fact.start + datetime.timedelta(minutes=15)
        with pytest.raises(ValueError):
            alchemy_store.facts._add(fact)

    def test_add_fails_timeframe_available_existing_fact_overlaps_end_only(
        self,
        alchemy_store,
        fact,
        alchemy_fact,
    ):
        """
        Make sure that passing a fact with only end overlapping an existing
        one raises error.
        """
        fact.start = alchemy_fact.end - datetime.timedelta(minutes=1)
        fact.end = alchemy_fact.end + datetime.timedelta(minutes=15)
        with pytest.raises(ValueError):
            alchemy_store.facts._add(fact)

    # Testcase for Bug LIB-253
    def test_add_fails_timeframe_available_fact_within_existing_timeframe(
        self,
        alchemy_store,
        fact,
        alchemy_fact,
    ):
        """
        Make sure that passing a fact that is completely within an existing
        ones raises error.
        """
        fact.start = alchemy_fact.start + datetime.timedelta(minutes=1)
        fact.end = alchemy_fact.end - datetime.timedelta(minutes=1)
        with pytest.raises(ValueError):
            alchemy_store.facts._add(fact)

    def test_add_fails_timeframe_available_fact_spans_existing_timeframe(
        self,
        alchemy_store,
        fact,
        alchemy_fact,
    ):
        """
        Make sure that passing a fact that completely spans an existing fact
        raises an error.
        """
        fact.start = alchemy_fact.start - datetime.timedelta(minutes=1)
        fact.end = alchemy_fact.end + datetime.timedelta(minutes=15)
        with pytest.raises(ValueError):
            alchemy_store.facts._add(fact)

    # ***

    def test_add_tags(self, alchemy_store, fact):
        """Make sure that adding a new valid fact will also save its tags."""
        result = alchemy_store.facts._add(fact)
        assert fact.tags
        db_instance = alchemy_store.session.query(AlchemyFact).get(result.pk)
        assert db_instance.tags
        assert db_instance.as_hamster(alchemy_store).equal_fields(fact)

    def test_add_new_valid_fact_new_activity(self, alchemy_store, fact):
        """
        Make sure that adding a new valid fact with a new activity works as
        intended.
        """
        assert alchemy_store.session.query(AlchemyFact).count() == 0
        assert alchemy_store.session.query(AlchemyActivity).count() == 0
        result = alchemy_store.facts._add(fact)
        db_instance = alchemy_store.session.query(AlchemyFact).get(result.pk)
        assert alchemy_store.session.query(AlchemyFact).count() == 1
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert db_instance.as_hamster(alchemy_store).equal_fields(fact)

    def test_add_new_valid_fact_existing_activity(
        self,
        alchemy_store,
        fact,
        alchemy_activity,
    ):
        """
        Make sure that adding a new valid fact with an existing activity works
        as intended.
        """
        fact.activity = alchemy_activity.as_hamster(alchemy_store)
        assert alchemy_store.session.query(AlchemyFact).count() == 0
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        result = alchemy_store.facts._add(fact)
        db_instance = alchemy_store.session.query(AlchemyFact).get(result.pk)
        assert alchemy_store.session.query(AlchemyFact).count() == 1
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert db_instance.as_hamster(alchemy_store).equal_fields(fact)

    def test_add_fails_pk_not_none(self, alchemy_store, fact):
        """Make sure that passing a fact with a PK raises error."""
        fact.pk = 101
        with pytest.raises(ValueError):
            alchemy_store.facts._add(fact)

    # ***

    def test_update_respects_tags(self, alchemy_store, alchemy_fact, new_fact_values):
        """Make sure that updating sets tags as expected."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        new_values = new_fact_values(fact)
        fact.tags = new_values["tags"]
        result = alchemy_store.facts._update(fact)
        # Because split_from, fact will have been marked deleted.
        assert fact.deleted
        # And the new Fact will have a larger PK.
        # (lb): We really don't need to impose a strictly increasing order
        # property on the PK, but it's how our code happens to work, so might
        # as well check it.
        assert result.pk > fact.pk
        fact.deleted = False
        assert result.split_from.pk == fact.pk
        # Note that the split-from is not the same because it contains previous tags.
        assert result.split_from != fact
        db_instance = alchemy_store.session.query(AlchemyFact).get(result.pk)
        assert db_instance.as_hamster(alchemy_store).equal_fields(result)
        result.split_from = None
        assert result.equal_fields(fact)

    def test_update_fails_pk_unknown(
        self, alchemy_store, alchemy_fact, new_fact_values
    ):
        """Make sure that trying to update a fact that does not exist raises error."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        new_values = new_fact_values(fact)
        fact.start = new_values["start"]
        fact.end = new_values["end"]
        fact.pk += 100
        with pytest.raises(KeyError):
            alchemy_store.facts._update(fact)

    def test_update_fails_pk_none(self, alchemy_store, alchemy_fact, new_fact_values):
        """Make sure that trying to update a new fact ,e.g. one without a pk."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        new_values = new_fact_values(fact)
        fact.start = new_values["start"]
        fact.end = new_values["end"]
        fact.pk = None
        with pytest.raises(ValueError):
            alchemy_store.facts._update(fact)

    # ***

    def test_save_new(self, fact, alchemy_store):
        count_before = alchemy_store.session.query(AlchemyFact).count()
        result = alchemy_store.facts.save(fact)
        count_after = alchemy_store.session.query(AlchemyFact).count()
        assert count_before < count_after
        assert result.activity.name == fact.activity.name
        assert result.description == fact.description

    # ***

    def test_remove_normal(self, alchemy_store, alchemy_fact):
        """Make sure the fact but not its tags are removed."""
        count_before = alchemy_store.session.query(AlchemyFact).count()
        tags_before = alchemy_store.session.query(AlchemyTag).count()
        fact = alchemy_fact.as_hamster(alchemy_store)
        alchemy_store.facts.remove(fact, purge=True)
        count_after = alchemy_store.session.query(AlchemyFact).count()
        assert count_after < count_before
        assert alchemy_store.session.query(AlchemyFact).get(fact.pk) is None
        assert alchemy_store.session.query(AlchemyTag).count() == tags_before

    def test_remove_fails_no_pk(self, alchemy_store, alchemy_fact):
        """Ensure remove() raises ValueError when passed Fack without PK."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        fact.pk = None
        with pytest.raises(ValueError):
            alchemy_store.facts.remove(fact)

    def test_remove_fails_unknown_pk(self, alchemy_store, alchemy_fact):
        """Ensure remove() raises ValueError when passed Fack with unknown PK."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        fact.pk += 1
        with pytest.raises(KeyError):
            alchemy_store.facts.remove(fact)

    def test_remove_fails_already_deleted(self, alchemy_store, alchemy_fact):
        """Ensure remove() raises ValueError when passed Fack marked deleted."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        fact.deleted = True
        alchemy_store.facts.save(fact)
        with pytest.raises(Exception):
            alchemy_store.facts.remove(fact)

    # ***

    def test_get(self, alchemy_store, alchemy_fact):
        fact = alchemy_fact.as_hamster(alchemy_store)
        result = alchemy_store.facts.get(fact.pk)
        assert result == fact

    # Most of the get_all tests are in test_gather_fact, except this one.
    @freeze_time("2015-12-12 18:00")
    def test_get_all_since_until(
        self,
        alchemy_store,
        mocker,
        fact,
        search_parameter_parametrized,
    ):
        """Ensure since and until are converted to datetime for backend function."""
        # See also: nark's test_get_all_various_since_and_until_times
        since, until, description, expectation = search_parameter_parametrized
        mocker.patch.object(alchemy_store.facts, "gather", return_value=[fact])
        # F841 local variable '_facts' is assigned to but never used
        _facts = alchemy_store.facts.get_all(since=since, until=until)  # noqa: F841
        assert alchemy_store.facts.gather.called
        # call_args is (args, kwargs), and QueryTerms is the first args arg.
        query_terms = alchemy_store.facts.gather.call_args[0][0]
        assert query_terms.since == expectation["since"]
        assert query_terms.until == expectation["until"]

    # ***

    def test_starting_at(self, alchemy_store, alchemy_fact):
        """Verify FactManager.starting_at."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        # Ensure that starting_at does not exclude the reference Fact.
        ref = fact.copy(include_pk=False)
        result = alchemy_store.facts.starting_at(ref)
        assert result == fact

    # ***

    def test_ending_at(self, alchemy_store, alchemy_fact):
        """Verify FactManager.ending_at."""
        fact = alchemy_fact.as_hamster(alchemy_store)
        # Ensure that starting_at does not exclude the reference Fact.
        ref = fact.copy(include_pk=False)
        result = alchemy_store.facts.ending_at(ref)
        assert result == fact

    # ***

    @pytest.mark.parametrize("send_fact", (False, "closed", "active"))
    def test_antecedent(self, alchemy_store, set_of_alchemy_facts_active, send_fact):
        """Verify FactManager.antecedent works with various reference input."""
        assert len(set_of_alchemy_facts_active) == 5
        # Depending on send_fact, either send the fact, or a datetime.
        if send_fact:
            ref_time = None
            if send_fact == "closed":
                fact = set_of_alchemy_facts_active[3]
                expect = set_of_alchemy_facts_active[2]
            else:  # 'active'
                fact = set_of_alchemy_facts_active[4]
                expect = set_of_alchemy_facts_active[3]
        else:
            fact = None
            ref_time = set_of_alchemy_facts_active[3].start
            expect = set_of_alchemy_facts_active[2]
        result = alchemy_store.facts.antecedent(fact=fact, ref_time=ref_time)
        assert result == expect

    # ***

    @pytest.mark.parametrize("send_fact", (False, True))
    def test_subsequent(self, alchemy_store, set_of_alchemy_facts, send_fact):
        """Verify FactManager.subsequent works with various reference input."""
        assert len(set_of_alchemy_facts) == 5
        fact_2nd = set_of_alchemy_facts[1]
        fact_3rd = set_of_alchemy_facts[2]
        # Depending on send_fact, either send the fact, or a datetime.
        fact = fact_2nd if send_fact else None
        ref_time = fact_2nd.end if not send_fact else None
        result = alchemy_store.facts.subsequent(fact=fact, ref_time=ref_time)
        # We could instead checked against a real Fact, either works:
        #  fact_3rd = set_of_alchemy_facts[2].as_hamster(alchemy_store)
        assert result == fact_3rd

    # ***

    def test_strictly_during(self, alchemy_store, set_of_alchemy_facts):
        """Verify FactManager.strictly_during finds a range of Facts."""
        assert len(set_of_alchemy_facts) == 5
        expect = set_of_alchemy_facts[1:2]
        results = alchemy_store.facts.strictly_during(
            since=expect[0].start,
            until=expect[-1].end,
        )
        assert results == expect

    # ***

    def test_surrounding_exclusive_outer(self, alchemy_store, set_of_alchemy_facts):
        """Verify exclusive surrounding finds nothing given a Fact's start or end."""
        assert len(set_of_alchemy_facts) == 5
        any_fact = set_of_alchemy_facts[2]
        fact_time = any_fact.start
        results = alchemy_store.facts.surrounding(fact_time=fact_time, inclusive=False)
        assert results == []

    def test_surrounding_exclusive_inner(self, alchemy_store, set_of_alchemy_facts):
        """Verify exclusive surrounding finds Fact given time between start and end."""
        assert len(set_of_alchemy_facts) == 5
        any_fact = set_of_alchemy_facts[2]
        fact_time = any_fact.end - ((any_fact.end - any_fact.start) / 2)
        results = alchemy_store.facts.surrounding(fact_time=fact_time, inclusive=False)
        assert results[0] == any_fact

    def test_surrounding_inclusive_outer(
        self,
        alchemy_store,
        set_of_alchemy_facts_contiguous,
    ):
        """Verify inclusive surrounding finds 2 Facts given time at end and start."""
        assert len(set_of_alchemy_facts_contiguous) == 5
        expect = [
            set_of_alchemy_facts_contiguous[1],
            set_of_alchemy_facts_contiguous[2],
        ]
        fact_time = expect[-1].start
        results = alchemy_store.facts.surrounding(fact_time=fact_time, inclusive=True)
        assert results == expect

    def test_surrounding_inclusive_inner(self, alchemy_store, set_of_alchemy_facts):
        """Verify inclusive surrounding finds Fact given time between start and end."""
        assert len(set_of_alchemy_facts) == 5
        any_fact = set_of_alchemy_facts[2]
        fact_time = any_fact.end - ((any_fact.end - any_fact.start) / 2)
        results = alchemy_store.facts.surrounding(fact_time=fact_time, inclusive=True)
        assert results[0] == any_fact

    # ***

    def test_endless(self, alchemy_store, set_of_alchemy_facts_active):
        """Verify FactManager.endless finds the active Fact."""
        assert len(set_of_alchemy_facts_active) == 5
        expect = set_of_alchemy_facts_active[-1]
        results = alchemy_store.facts.endless()
        assert results[0] == expect

    # ***
