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

from nark.managers.query_terms import QueryTerms

# ***


class TestFactManager:
    def test_save_fact_endless_active(self, basestore, fact, mocker):
        """
        Make sure that passing a fact without end (aka 'endless, ongoing,
        active fact') triggers the correct method.
        """
        magic_fact = {}
        mocker.patch.object(basestore.facts, "_add", return_value=magic_fact)
        fact.end = None
        new_fact = basestore.facts.save(fact)
        assert basestore.facts._add.called
        assert new_fact is magic_fact

    def test_save_fact_too_brief_value_error(self, basestore, fact):
        """Ensure that a fact with too small of a time delta raises an exception."""
        delta = datetime.timedelta(
            seconds=(basestore.config["time.fact_min_delta"] - 1)
        )
        fact.end = fact.start + delta
        with pytest.raises(ValueError):
            basestore.facts.save(fact)

    def test_save_fact_no_fact_min_delta(self, basestore, fact, mocker):
        """Ensure that a fact with too small of a time delta raises an exception."""
        magic_fact = {}
        mocker.patch.object(basestore.facts, "_add", return_value=magic_fact)
        # Note that out config defined the type as int, so use 0, not None.
        basestore.config["time.fact_min_delta"] = 0
        fact.end = fact.start
        new_fact = basestore.facts.save(fact)
        assert basestore.facts._add.called
        assert new_fact is magic_fact

    def test_add_not_implemented(self, basestore, fact):
        with pytest.raises(NotImplementedError):
            basestore.facts._add(fact)

    def test_update_not_implemented(self, basestore, fact):
        with pytest.raises(NotImplementedError):
            basestore.facts._update(fact)

    def test_remove_not_implemented(self, basestore, fact):
        with pytest.raises(NotImplementedError):
            basestore.facts.remove(fact)

    def test_get_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.get(12)

    def test_get_all_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            # Note that BaseManager.get_all actually *is* implemented, but
            # it calls self.gather(), which won't be implemented in basestore.
            # So this runs a little code (checking for and converting the 'since'
            # and 'until' arguments to datetime objects) before the raise.
            basestore.facts.get_all()

    def test_get_all_by_usage_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.get_all_by_usage()

    def test_gather_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.gather(query_terms=None)

    # *** get_all since/until argument tests.

    # (lb): I think these were from old hamster-lib where it made more sense
    # for these to be complicated. The code has been refactored so much that
    # these tests do a lot of work for not much code or unique branch coverage.

    @pytest.mark.parametrize(
        ("since", "until", "expectation"),
        [
            (None, None, {"since": None, "until": None}),
            # Various since info.
            (
                datetime.date(2014, 4, 1),
                None,
                {"since": datetime.datetime(2014, 4, 1, 5, 30, 0), "until": None},
            ),
            (
                datetime.time(13, 40, 25),
                None,
                {"since": datetime.datetime(2015, 4, 1, 13, 40, 25), "until": None},
            ),
            (
                datetime.datetime(2014, 4, 1, 13, 40, 25),
                None,
                {"since": datetime.datetime(2014, 4, 1, 13, 40, 25), "until": None},
            ),
            # Various until info.
            (
                None,
                datetime.date(2014, 2, 1),
                {"since": None, "until": datetime.datetime(2014, 2, 2, 5, 29, 59)},
            ),
            (
                None,
                datetime.time(13, 40, 25),
                {"since": None, "until": datetime.datetime(2015, 4, 1, 13, 40, 25)},
            ),
            (
                None,
                datetime.datetime(2014, 4, 1, 13, 40, 25),
                {"since": None, "until": datetime.datetime(2014, 4, 1, 13, 40, 25)},
            ),
        ],
    )
    @freeze_time("2015-04-01 18:00")
    def test_get_all_various_since_and_until_times(
        self,
        basestore,
        mocker,
        since,
        until,
        expectation,
    ):
        """Test that time conversion matches expectations."""
        mocker.patch.object(
            basestore.facts,
            "gather",
        )
        query_terms = QueryTerms(since=since, until=until)
        # MAYBE/2020-05-25: (lb): I don't quite like that get_all mutates query_terms.
        basestore.facts.get_all(query_terms)
        assert basestore.facts.gather.called
        actual_qt = basestore.facts.gather.call_args[0][0]
        expect_qt = QueryTerms(
            since=expectation["since"],
            until=expectation["until"],
        )
        assert actual_qt == expect_qt

    @pytest.mark.parametrize(
        ("since", "until"),
        [
            (
                datetime.date(2015, 4, 5),
                datetime.date(2012, 3, 4),
            ),
            (
                datetime.datetime(2015, 4, 5, 18, 0, 0),
                datetime.datetime(2012, 3, 4, 19, 0, 0),
            ),
        ],
    )
    def test_get_all_until_before_since(self, basestore, since, until):
        """Test that we throw an exception if passed until time is before since time."""
        with pytest.raises(ValueError):
            basestore.facts.get_all(since=since, until=until)

    @pytest.mark.parametrize(
        ("since", "until"),
        [
            # (lb): This test used to cause TypeError, because get_all used to not
            # parse the input, but expected datetime objects instead. So the string
            # values in the parameters here would trigger TypeError. But now the
            # parsing is part of get_all (because DRY), so now we test ValueError.
            # - Note that since > until here, so ValueError, and tests mixed types.
            (datetime.date(2015, 4, 5), "2012-03-04"),
            ("2015-04-05 18:00:00", "2012-03-04 19:00:00"),
        ],
    )
    def test_get_all_invalid_date_types(self, basestore, mocker, since, until):
        """Test that we throw an exception if we receive invalid date/time objects."""
        with pytest.raises(ValueError):
            basestore.facts.get_all(since=since, until=until)

    # ***

    @freeze_time("2015-10-03 14:45")
    def test_get_today(self, basestore, mocker):
        """Make sure that method uses appropriate timeframe."""
        mocker.patch.object(basestore.facts, "get_all", return_value=[])
        results = basestore.facts.get_today()
        assert results == []
        assert basestore.facts.get_all.call_args[1] == {
            "since": datetime.datetime(2015, 10, 3, 5, 30, 0),
            "until": datetime.datetime(2015, 10, 4, 5, 29, 59),
        }

    @freeze_time("2015-10-03 14:45")
    def test_day_end_datetime_no_end_date(self, basestore):
        """Make sure that method uses appropriate timeframe."""
        basestore.config["time.day_start"] = datetime.time(5, 30)
        until = basestore.facts.day_end_datetime(end_date=None)
        assert until == datetime.datetime(2015, 10, 4, 5, 29, 59)

    # *** stop_current_fact tests.

    @freeze_time("2019-02-01 18:00")
    @pytest.mark.parametrize(
        "hint",
        (
            None,
            datetime.timedelta(minutes=10),
            datetime.timedelta(minutes=300),
            datetime.timedelta(seconds=-10),
            datetime.timedelta(minutes=-10),
            datetime.datetime(2019, 2, 1, 19),
        ),
    )
    def test_stop_current_fact_with_hint(
        self,
        basestore,
        base_config,
        endless_fact,
        hint,
        mocker,
    ):
        """
        Make sure we can stop an 'ongoing fact' and that it will have an end set.

        Please note that ever so often it may happen that the factory generates
        a endless_fact with ``Fact.start`` after our mocked today-date. In order
        to avoid confusion the easies fix is to make sure the mock-today is well
        in the future.
        """
        now = datetime.datetime.now()  # the freeze_time time, above.
        # (lb): The FactFactory sets start to faker.Faker().date_time(),
        # which is not constrained in any way, and might set Fact.start in
        # the future, or close to now (freeze_time), in which case our 'hint'
        # value might otherwise cause the test to end the Fact before it
        # starts, eliciting the complaint:
        #   ValueError:
        #       Cannot end the Fact before it started.
        #       Try editing the Fact instead.
        # So ensure that setting end (relative to now) won't fail, by
        # possibly moving Fact.start. (lb): Does it make setting Fact.start
        # to a fake time worth it if we have to possibly change it anyway?
        # - Start with the fact_min_delta padding, which will also cause a
        #   complaint, if end isn't far enough ahead of start.
        max_delta_secs = base_config["time"]["fact_min_delta"]
        if hint and isinstance(hint, datetime.timedelta) and hint.total_seconds() < 0:
            # Subtract hint's seconds, which is a negative value, so really,
            # increase the max_delta_secs, because hint will be subtracted
            # from now later (expected_end = now + hint).
            max_delta_secs -= hint.total_seconds()
        max_start = None
        if max_delta_secs:
            max_start = now - datetime.timedelta(seconds=max_delta_secs)
        if endless_fact.start > max_start:
            endless_fact.start = max_start
        # NOTE: The `fact` fixture simply adds a second Fact to the db, after
        #       having added the endless_fact Fact.
        if hint:
            if isinstance(hint, datetime.datetime):
                expected_end = hint
            else:
                # Add hint to now, e.g., datetime.datetime(2019, 2, 1, 18) + hint.
                expected_end = now + hint
        else:
            # NOTE: Because freeze_time, datetime.now() === datetime.utcnow().
            expected_end = datetime.datetime.now().replace(microsecond=0)
        mocker.patch.object(basestore.facts, "endless", return_value=[endless_fact])
        mocker.patch.object(
            basestore.facts,
            "_add",
        )
        basestore.facts.stop_current_fact(hint)
        assert basestore.facts.endless.called
        assert basestore.facts._add.called
        fact_to_be_added = basestore.facts._add.call_args[0][0]
        assert fact_to_be_added.end == expected_end
        fact_to_be_added.end = None
        assert fact_to_be_added == endless_fact

    @freeze_time("2019-02-01 18:00")
    @pytest.mark.parametrize("hint", (datetime.datetime(2019, 2, 1, 17, 59),))
    def test_stop_current_fact_with_end_in_the_past(
        self,
        basestore,
        base_config,
        endless_fact,
        hint,
        mocker,
    ):
        """
        Make sure that stopping an 'ongoing fact' with end before start raises.
        """
        # Set start to the freeze_time time, above.
        endless_fact.start = datetime.datetime.now()
        mocker.patch.object(basestore.facts, "endless", return_value=[endless_fact])
        mocker.patch.object(
            basestore.facts,
            "_add",
        )
        with pytest.raises(ValueError):
            basestore.facts.stop_current_fact(hint)
        assert basestore.facts.endless.called
        assert not basestore.facts._add.called

    def test_stop_current_fact_invalid_offset_hint(
        self,
        basestore,
        endless_fact,
        mocker,
    ):
        """
        Make sure that stopping with an offset hint that results in end > start
        raises an error.
        """
        mocker.patch.object(basestore.facts, "endless", return_value=[endless_fact])
        now = datetime.datetime.now().replace(microsecond=0)
        offset = (now - endless_fact.start).total_seconds() + 100
        offset = datetime.timedelta(seconds=-1 * offset)
        with pytest.raises(ValueError):
            basestore.facts.stop_current_fact(offset)

    def test_stop_current_fact_invalid_datetime_hint(
        self,
        basestore,
        endless_fact,
        mocker,
    ):
        """
        Make sure that stopping with a datetime hint that results in end > start
        raises an error.
        """
        mocker.patch.object(basestore.facts, "endless", return_value=[endless_fact])
        with pytest.raises(ValueError):
            basestore.facts.stop_current_fact(
                endless_fact.start - datetime.timedelta(minutes=30),
            )

    def test_stop_current_fact_invalid_hint_type(
        self,
        basestore,
        endless_fact,
        mocker,
    ):
        """Make sure that passing an invalid hint type raises an error."""
        mocker.patch.object(basestore.facts, "endless", return_value=[endless_fact])
        with pytest.raises(TypeError):
            basestore.facts.stop_current_fact(str())

    # ***

    # Note that get_current_fact() also gets tested by way of
    # stop_current_fact(), as well as find_latest_fact().

    def test_get_current_fact_datebase_integrity_issue_multiple_active_facts(
        self,
        basestore,
        endless_fact,
        mocker,
    ):
        """Make sure that if 2 Facts are Active, get_current_fact fails."""
        two_endless = [endless_fact, endless_fact]
        mocker.patch.object(basestore.facts, "endless", return_value=two_endless)
        with pytest.raises(Exception):
            basestore.facts.get_current_fact()

    # *** find_latest_fact

    def test_find_latest_fact_finds_fact_ongoing_exists(
        self,
        basestore,
        endless_fact,
        mocker,
    ):
        """Ensure find_latest_fact finds 'ongoing' Fact."""
        mocker.patch.object(basestore.facts, "endless", return_value=[endless_fact])
        restrict = "ongoing"
        found = basestore.facts.find_latest_fact(restrict=restrict)
        assert found is endless_fact

    def test_find_latest_fact_finds_fact_ongoing_not_found(
        self,
        basestore,
        endless_fact,
        mocker,
    ):
        """Ensure find_latest_fact returns None when no 'ongoing' Fact."""
        mocker.patch.object(basestore.facts, "endless", return_value=[])
        restrict = "ongoing"
        found = basestore.facts.find_latest_fact(restrict=restrict)
        assert found is None

    def test_find_latest_fact_finds_fact_ongoing_too_many(
        self,
        basestore,
        endless_fact,
        mocker,
    ):
        """Ensure find_latest_fact raises when there is more than 1 'ongoing' Fact."""
        two_endless = [endless_fact, endless_fact]
        mocker.patch.object(basestore.facts, "endless", return_value=two_endless)
        restrict = "ongoing"
        with pytest.raises(Exception):
            basestore.facts.find_latest_fact(restrict=restrict)

    def test_find_latest_fact_finds_fact_ended(
        self,
        basestore,
        fact,
        mocker,
    ):
        """Ensure find_latest_fact find an 'ended' Fact."""
        mocker.patch.object(basestore.facts, "get_all", return_value=[fact])
        restrict = "ended"
        found = basestore.facts.find_latest_fact(restrict=restrict)
        assert found is fact

    # *** find_oldest_fact

    def test_find_oldest_fact_found(
        self,
        basestore,
        fact,
        mocker,
    ):
        """Ensure find_oldest_fact find a fact when get_all returns one."""
        mocker.patch.object(basestore.facts, "get_all", return_value=[fact])
        found = basestore.facts.find_oldest_fact()
        assert found is fact

    def test_find_oldest_fact_not_found(
        self,
        basestore,
        fact,
        mocker,
    ):
        """Ensure find_oldest_fact find a fact when get_all returns none."""
        mocker.patch.object(basestore.facts, "get_all", return_value=[])
        found = basestore.facts.find_oldest_fact()
        assert found is None

    # *** endless

    def test_get_endless_fact_with_ongoing_fact(
        self,
        basestore,
        endless_fact,
        fact,
        mocker,
    ):
        """Make sure we return the 'ongoing_fact'."""
        mocker.patch.object(basestore.facts, "endless", return_value=[endless_fact])
        fact = basestore.facts.endless()
        assert fact == fact
        assert fact is fact

    def test_get_endless_fact_without_ongoing_fact(self, basestore, mocker):
        """Make sure that we raise a KeyError if there is no 'ongoing fact'."""
        mocker.patch.object(basestore.facts, "endless", return_value=[])
        fact = basestore.facts.endless()
        assert fact == []

    # *** cancel_current_fact

    def test_cancel_current_fact(self, basestore, endless_fact, fact, mocker):
        """Make sure we return the 'ongoing_fact'."""
        mocker.patch.object(basestore.facts, "endless", return_value=[endless_fact])
        mocker.patch.object(
            basestore.facts,
            "remove",
        )
        result = basestore.facts.cancel_current_fact()
        assert basestore.facts.endless.called
        assert basestore.facts.remove.called
        assert result is endless_fact  # Because mocked.
        # FIXME: Where's the test that actually tests FactManager.endless()?

    def test_cancel_current_fact_without_endless_fact(self, basestore, mocker):
        """Make sure that we raise a KeyError if there is no 'ongoing fact'."""
        mocker.patch.object(basestore.facts, "endless", return_value=[])
        with pytest.raises(KeyError):
            basestore.facts.cancel_current_fact()
        assert basestore.facts.endless.called

    # ***

    def test_starting_at_not_implemented(self, basestore, fact):
        with pytest.raises(NotImplementedError):
            basestore.facts.starting_at(fact)

    def test_ending_at_not_implemented(self, basestore, fact):
        with pytest.raises(NotImplementedError):
            basestore.facts.ending_at(fact)

    def test_antecedent_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.antecedent()

    def test_subsequent_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.subsequent()

    def test_strictly_during_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.strictly_during(start=None, end=None)

    def test_surrounding_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.surrounding(fact_time=None)

    def test_endless_not_implemented(self, basestore):
        with pytest.raises(NotImplementedError):
            basestore.facts.endless()
