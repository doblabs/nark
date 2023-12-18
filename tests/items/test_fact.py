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
import datetime
from math import inf
from operator import attrgetter

import faker as faker_
import pytest
from freezegun import freeze_time

from nark.items.activity import Activity
from nark.items.category import Category
from nark.items.fact import Fact
from nark.items.tag import Tag

from .test_activity import TestActivity
from .test_tag import TestTag

faker = faker_.Faker()


# A class to test as_kvals.
class FactWithFact(Fact):
    def __init__(self, *args, **kwargs):
        super(FactWithFact, self).__init__(*args, **kwargs)
        self.mirror = self


class TestFact(object):
    """items.fact.Fact class tests."""

    def test_fact_init_valid(
        self,
        activity,
        start_end_datetimes,
        pk_valid_parametrized,
        description_valid_parametrized,
        tag_list_valid_parametrized,
    ):
        """Make sure valid values instaniate a Fact."""
        fact = Fact(
            activity,
            start_end_datetimes[0],
            start_end_datetimes[1],
            pk_valid_parametrized,
            description_valid_parametrized,
            tag_list_valid_parametrized,
        )
        assert fact.activity == activity
        assert fact.pk == pk_valid_parametrized
        assert fact.description == description_valid_parametrized
        assert fact.start == start_end_datetimes[0]
        assert fact.end == start_end_datetimes[1]
        # tag_list_valid_parametrized is a set() of name strings.
        names = list(tag_list_valid_parametrized)
        tags = set([Tag(pk=None, name=name) for name in names])
        tags = sorted(list(tags), key=attrgetter("name"))
        assert fact.tags_sorted == tags

    # ***

    @pytest.mark.parametrize(
        ("factoid", "time_hint", "lenient", "should_err"),
        [
            (
                "12:00 - 14:00 foo@bar, bazbat",
                "verify_both",
                False,
                None,
            ),
            (
                "12:00 - 14:00 foo",
                "verify_both",
                True,
                "Expected to find an Activity name.",
            ),
            (
                "foo@bar",
                "verify_none",
                True,
                None,
            ),
            (
                "12:00-14:00 foo@bar",
                "verify_both",
                False,
                None,
            ),
            # Test seconds (2018-08-16: they no longer get truncated).
            (
                "12:00:11 - 14:00:59 baz@bat",
                "verify_both",
                False,
                None,
            ),
            # Test just start and end, no activity, category, tags, nor description.
            (
                "12:00:11 - 13:01",
                "verify_both",
                True,
                "Expected to find an Activity name.",
            ),
            # Test just a start time.
            (
                "13:01:22",
                "verify_start",
                True,
                "Expected to find an Activity name.",
            ),
        ],
    )
    def test_create_from_factoid_valid(self, factoid, time_hint, lenient, should_err):
        """Make sure that a valid raw fact creates a proper Fact."""
        fact, err = Fact.create_from_factoid(
            factoid,
            time_hint=time_hint,
            lenient=lenient,
        )
        assert fact
        assert str(err) == str(should_err)

    @pytest.mark.parametrize(
        ("raw_fact", "expectations"),
        [
            (
                # Note that without a time_hint, no time expected, so
                # start and end are None, and prefix (before colon) is
                # just part of the activity name.
                "-7 foo@bar, bazbat",
                {
                    "start": None,
                    "end": None,
                    "activity": "-7 foo",
                    "category": "bar",
                    "description": "bazbat",
                },
            ),
        ],
    )
    @freeze_time("2015-05-02 18:07")
    def test_create_from_factoid_with_delta_no_time_hint(self, raw_fact, expectations):
        fact, err = Fact.create_from_factoid(raw_fact)
        assert fact.start == expectations["start"]
        assert fact.end == expectations["end"]
        assert fact.activity.name == expectations["activity"]
        assert fact.activity.category.name == expectations["category"]
        assert fact.description == expectations["description"]
        assert not err

    @pytest.mark.parametrize(
        ("factoid", "expectations"),
        [
            (
                "-7 foo@bar, bazbat",
                {
                    # Note that time parsing does not occur until later, so that
                    # multiple Factoids can be parsed, and then relative times can
                    # be determined with reference to surrounding Facts. Although in
                    # this example, because start is relative to end, we could add code
                    # to resolve time relative to the Fact itself, but there's not a good
                    # reason to do so, e.g., here, after resolution, you'd see:
                    #   'start': datetime.datetime(2015, 5, 2, 18, 0, 0),
                    "start": "-7",
                    "end": None,
                    "activity": "foo",
                    "category": "bar",
                    "description": "bazbat",
                },
            ),
        ],
    )
    @freeze_time("2015-05-02 18:07")
    def test_create_from_factoid_with_delta_time_hint_start(
        self, factoid, expectations
    ):
        fact, err = Fact.create_from_factoid(factoid, time_hint="verify_start")
        assert fact.start == expectations["start"]
        assert fact.end == expectations["end"]
        assert fact.activity.name == expectations["activity"]
        assert fact.activity.category.name == expectations["category"]
        assert fact.description == expectations["description"]
        assert not err

    # ***

    @pytest.mark.parametrize(
        "start",
        [
            None,
            # The faker randomizes the microsecond field, but nark assumes 0.
            faker.date_time().replace(microsecond=0),
            "10",
            "+10",
            "-10h5m",
        ],
    )
    def test_start_valid(self, fact, start):
        """Make sure that valid arguments get stored by the setter."""
        fact.start = start
        assert fact.start == start

    @pytest.mark.parametrize(
        "start",
        [
            faker.date_time().strftime("%y-%m-%d %H:%M"),  # string, not datetime
            "not relative",
            "+10d",  # Not supported
        ],
    )
    def test_start_invalid(self, fact, start):
        """Make sure that trying to store dateimes as strings throws an error."""
        with pytest.raises(TypeError):
            fact.start = start

    @pytest.mark.parametrize(
        "end",
        [
            None,
            # The faker randomizes the microsecond field, but nark assumes 0.
            faker.date_time().replace(microsecond=0),
        ],
    )
    def test_end_valid(self, fact, end):
        """Make sure that valid arguments get stored by the setter."""
        fact.end = end
        assert fact.end == end

    def test_end_invalid(self, fact):
        """Make sure that trying to store dateimes as strings throws an error."""
        with pytest.raises(TypeError):
            # No need to replace microseconds, because %M truncates (m)secs.
            fact.end = faker.date_time().strftime("%y-%m-%d %H:%M")

    def test_description_valid(self, fact, description_valid_parametrized):
        """Make sure that valid arguments get stored by the setter."""
        fact.description = description_valid_parametrized
        assert fact.description == description_valid_parametrized

    def test_category_property(self, fact):
        """Make sure the property returns this facts category."""
        assert fact.category == fact.activity.category

    def test_serialized_string(self, fact):
        """
        Ensure a serialized string with full information matches our expectation.
        """
        expect_f = "{start} to {end} {activity}@{category}: #{tag}: {description}"
        expectation = expect_f.format(
            start=fact.start.strftime("%Y-%m-%d %H:%M:%S"),
            end=fact.end.strftime("%Y-%m-%d %H:%M:%S"),
            activity=fact.activity.name,
            category=fact.category.name,
            tag=sorted(list(fact.tags), key=attrgetter("name"))[0].name,
            description=fact.description,
        )
        result = fact.get_serialized_string()
        assert isinstance(result, str)
        assert result == expectation

    @pytest.mark.parametrize(
        ("values", "expectation"),
        (
            (
                {
                    "start": datetime.datetime(2016, 1, 1, 18),
                    "end": datetime.datetime(2016, 1, 1, 19),
                    "activity": Activity("homework", category=Category("school")),
                    "tags": set([Tag("math"), Tag("science")]),
                    "description": "something clever ...",
                },
                "2016-01-01 18:00:00 to 2016-01-01 19:00:00 "
                "homework@school: #math #science: something clever ...",
            ),
            (
                {
                    "start": datetime.datetime(2016, 1, 1, 18),
                    "end": datetime.datetime(2016, 1, 1, 19),
                    "activity": Activity("homework", category=None),
                    "tags": set([Tag("math"), Tag("science"), Tag("science fiction")]),
                    "description": "something",
                },
                "2016-01-01 18:00:00 to 2016-01-01 19:00:00 "
                "homework@: #math #science #science fiction: something",
            ),
            (
                {
                    "start": datetime.datetime(2016, 1, 1, 18),
                    "end": datetime.datetime(2016, 1, 1, 19),
                    "activity": Activity("homework", category=Category("school")),
                    "tags": set(),
                    "description": "something clever ...",
                },
                "2016-01-01 18:00:00 to 2016-01-01 19:00:00 "
                "homework@school: something clever ...",
            ),
            (
                {
                    "start": datetime.datetime(2016, 1, 1, 18),
                    "end": datetime.datetime(2016, 1, 1, 19),
                    "activity": Activity("homework", category=Category("school")),
                    "tags": set([Tag("science"), Tag("math")]),
                    "description": "",
                },
                "2016-01-01 18:00:00 to 2016-01-01 19:00:00 "
                "homework@school: #math #science",
            ),
            (
                {
                    "start": datetime.datetime(2016, 1, 1, 18),
                    "end": datetime.datetime(2016, 1, 1, 19),
                    "activity": Activity("homework", category=Category("school")),
                    "tags": set(),
                    "description": "",
                },
                "2016-01-01 18:00:00 to 2016-01-01 19:00:00 " "homework@school",
            ),
            (
                {
                    "start": None,
                    "end": datetime.datetime(2016, 1, 1, 19),
                    "activity": Activity("homework", category=Category("school")),
                    "tags": set([Tag("math"), Tag("science")]),
                    "description": "something clever ...",
                },
                # FIXME/2018-08-17 12:25: Update factoid parse to recognize
                # 'to' and 'at' prefix to distinguish between verify_end, verify_start?
                # and then anything else is verify_both or verify_none?? hrmmmm...
                # maybe the answer is a 2nd parse-factoid wrapper, i.e.,
                #   one parser for verify_hint, and one parser for unknown-hint...
                "2016-01-01 19:00:00 homework@school: #math #science: something clever ...",
            ),
            (
                {
                    "start": None,
                    "end": None,
                    "activity": Activity("homework", category=Category("school")),
                    "tags": set([Tag("math"), Tag("science")]),
                    "description": "something clever ...",
                },
                # FIXME: Make new parse wrapper that checks for 'to' 'at', or date.
                #   Then look for 'to <date>', 'at <date>', etc.
                #   Fall back to what? Expect no dates? Both dates?
                #   Problem really is that I feel a Fact with no start or end
                #     is really an invalid Fact!! So this Factoid should be a
                #     problem, right?:
                "homework@school: #math #science: something clever ...",
            ),
            (
                {
                    "start": datetime.datetime(2016, 1, 1, 18),
                    "end": None,
                    "activity": Activity("homework", category=Category("school")),
                    "tags": set([Tag("math"), Tag("science")]),
                    "description": "something clever ...",
                },
                "at 2016-01-01 18:00:00 "
                "homework@school: #math #science: something clever ...",
            ),
        ),
    )
    def test_serialized_string_various_missing_values(self, fact, values, expectation):
        """
        Make sure the serialized string is correct even if some information is missing.
        """
        for attribute, value in values.items():
            setattr(fact, attribute, value)
        assert fact.get_serialized_string() == expectation

    def test__eq__false(self, fact):
        """Make sure that two distinct facts return ``False``."""
        other = copy.deepcopy(fact)
        other.pk = 1
        assert fact is not other
        assert fact != other

    def test__eq__true(self, fact):
        """Make sure that two identical facts return ``True``."""
        other = copy.deepcopy(fact)
        assert fact is not other
        assert fact == other

    def test_is_hashable(self, fact):
        """Test that ``Fact`` instances are hashable."""
        assert hash(fact)

    def test_hash_method(self, fact):
        """Test that ``__hash__`` returns the hash expected."""
        assert hash(fact) == hash(fact.as_tuple())

    def test_hash_different_between_instances(self, fact_factory):
        """
        Test that different instances have different hashes.

        This is actually unneeded as we are merely testing the builtin ``hash``
        function and ``Fact.as_tuple`` but for reassurance we test it anyway.
        """
        assert hash(fact_factory()) != hash(fact_factory())

    def test__gt__(self, fact):
        # A little self-referential, but covers it!
        assert not (fact > fact)

    def test__lt__(self, fact):
        # A little self-referential, but covers it!
        assert not (fact < fact)

    def test_sorty_times(self, fact):
        assert fact.sorty_times == (fact.start, fact.end)

    def test_sorty_tuple_inf(self, fact):
        assert fact.pk is None  # Which sorty_tuple replaces with -inf.
        assert fact.sorty_tuple == (fact.start, fact.end, -inf)

    def test_sorty_tuple_pk(self, fact):
        fact.pk = 123
        assert fact.sorty_tuple == (fact.start, fact.end, fact.pk)

    def test_as_kvals_avoid_repr_recursion(self):
        fact = FactWithFact(activity=None, start=None)
        repred = fact.as_kvals()
        assert repred.startswith("Fact(")

    def test_copy_include_pk(self, fact):
        new_fact = fact.copy(include_pk=True)
        assert new_fact == fact

    def test_as_tuple_include_pk(self, fact):
        """Make sure that conversion to a tuple matches our expectations."""
        assert fact.as_tuple() == (
            fact.pk,
            fact.activity.as_tuple(include_pk=True),
            fact.start,
            fact.end,
            fact.description,
            frozenset(fact.tags),
            fact.deleted,
            fact.split_from,
        )

    def test_as_tuple_exclude_pk(self, fact):
        """Make sure that conversion to a tuple matches our expectations."""
        assert fact.as_tuple(include_pk=False) == (
            False,
            fact.activity.as_tuple(include_pk=False),
            fact.start,
            fact.end,
            fact.description,
            frozenset([tag.as_tuple(include_pk=False) for tag in fact.tags]),
            fact.deleted,
            fact.split_from,
        )

    def test_equal_fields_true(self, fact):
        """Make sure that two facts that differ only in their PK compare equal."""
        other = copy.deepcopy(fact)
        other.pk = 1
        assert fact.equal_fields(other)

    def test_equal_fields_false(self, fact):
        """Make sure that two facts that differ not only in their PK compare unequal."""
        other = copy.deepcopy(fact)
        other.pk = 1
        other.description += "foobar"
        assert fact.equal_fields(other) is False

    # ***

    def test_start_fmt(self, fact):
        assert fact.start_fmt() == fact.start.strftime("%Y-%m-%d %H:%M:%S")

    def test_start_fmt_utc_empty(self):
        fact = Fact(activity=None, start=None)
        assert fact.start_fmt_utc == ""

    def test_start_fmt_utc_valid(self, fact):
        formatted = fact.start_fmt_utc
        assert formatted == fact.start.strftime("%Y-%m-%d %H:%M:%S%z")

    def test_start_fmt_local_empty(self):
        fact = Fact(activity=None, start=None)
        assert fact.start_fmt_local == ""

    def test_start_fmt_local_valid(self, fact):
        formatted = fact.start_fmt_local
        assert formatted == fact.start.strftime("%Y-%m-%d %H:%M:%S%z")

    # ***

    def test_end_fmt(self, fact):
        assert fact.end_fmt() == fact.end.strftime("%Y-%m-%d %H:%M:%S")

    def test_end_fmt_utc_empty(self):
        fact = Fact(activity=None, start=None, end=None)
        assert fact.end_fmt_utc == ""

    def test_end_fmt_utc_valid(self, fact):
        formatted = fact.end_fmt_utc
        assert formatted == fact.end.strftime("%Y-%m-%d %H:%M:%S%z")

    def test_end_fmt_local_empty(self):
        fact = Fact(activity=None, start=None, end=None)
        assert fact.end_fmt_local == ""

    def test_end_fmt_local_valid(self, fact):
        formatted = fact.end_fmt_local
        assert formatted == fact.end.strftime("%Y-%m-%d %H:%M:%S%z")

    @freeze_time("2015-05-02 18:07")
    def test_end_fmt_local_nowwed_now(self):
        fact = Fact(activity=None, start=None, end=None)
        formatted = fact.end_fmt_local_nowwed
        assert formatted == "2015-05-02 18:07:00 <now>"

    @freeze_time("2015-05-02 18:07")
    def test_end_fmt_local_nowwed_end(self, fact):
        formatted = fact.end_fmt_local_nowwed
        assert formatted == fact.end.strftime("%Y-%m-%d %H:%M:%S")

    #    @freeze_time('2015-05-02 18:07')
    #    def test_end_fmt_local_nowwed_now(self):
    #        fact = Fact(activity=None, start=None, end=None)
    #        formatted = fact.end_fmt_local_nowwed
    #        assert formatted == '2015-05-02 18:07:00 <now>'

    @freeze_time("2015-05-02 18:07")
    def test_end_fmt_local_or_now_end(self, fact):
        formatted = fact.end_fmt_local_or_now
        assert formatted == fact.end.strftime("%Y-%m-%d %H:%M:%S")

    @freeze_time("2015-05-02 18:07")
    def test_end_fmt_local_or_now_now(self):
        fact = Fact(activity=None, start=None, end=None)
        formatted = fact.end_fmt_local_or_now
        assert formatted == "2015-05-02 18:07:00"

    # ***

    def test_momentaneous_False(self, fact):
        assert not fact.momentaneous

    def test_momentaneous_True(self, fact):
        fact.end = fact.start
        assert fact.momentaneous

    @freeze_time("2015-05-02 18:07")
    def test_time_now(self, fact):
        # (lb): What's the point of accessing 'now' through the Fact? I forget.
        assert fact.time_now == datetime.datetime.now()

    def test_times(self, fact):
        # Note that Fact.times is similar to Fact.sorty_times, except latter
        # replaces Fact.end with UntilTimeStops if fact.end is None.
        assert fact.times == (fact.start, fact.end)

    def test_times_ok_True(self, fact):
        assert fact.times_ok is True

    def test_times_ok_False(self):
        fact = Fact(activity=None, start=None)
        assert fact.times_ok is False

    # ***

    def test_delta(self, fact):
        """Make sure that valid arguments get stored by the setter."""
        assert fact.delta() == fact.end - fact.start

    @freeze_time("2015-05-02 18:07")
    def test_delta_no_end(self, fact):
        """Make sure that a missing end datetime results in ``delta=None``."""
        # See FactFactory for default start/end.
        fact.end = None
        # NOTE: With freezegun, both now() and utcnow() are the same.
        assert fact.delta() == (datetime.datetime.now() - fact.start)

    @pytest.mark.parametrize(
        "offset",
        [
            (
                15,
                {
                    "%M": "15",
                    "%H:%M": "00:15",
                    "HHhMMm": " 0 hours 15 minutes",
                    "": "15.00 mins.",
                },
            ),
            (
                452,
                {
                    "%M": "452",
                    "%H:%M": "07:32",
                    "HHhMMm": " 7 hours 32 minutes",
                    "": "7.53 hours",
                },
            ),
            (
                912,
                {
                    "%M": "912",
                    "%H:%M": "15:12",
                    "HHhMMm": "15 hours 12 minutes",
                    "": "15.20 hours",
                },
            ),
            (
                61,
                {
                    "%M": "61",
                    "%H:%M": "01:01",
                    "HHhMMm": " 1 hour   1 minute ",
                    "": "1.02 hours",
                },
            ),
        ],
    )
    def test_format_delta_valid_style(
        self,
        fact,
        offset,
        start_end_datetimes_from_offset_now,
        string_delta_style_parametrized,
    ):
        """Make sure that the resulting string matches our expectation."""
        end_offset, expectation = offset
        fact.start, fact.end = start_end_datetimes_from_offset_now(end_offset)
        result = fact.format_delta(style=string_delta_style_parametrized)
        assert result == expectation[string_delta_style_parametrized]

    def test_format_delta_invalid_style(self, fact):
        """Ensure that passing an invalid format will raise an exception."""
        with pytest.raises(ValueError):
            fact.format_delta(style="foobar")

    # ***

    def test_midpoint_invalid(self):
        fact = Fact(activity=None, start=None)
        assert fact.midpoint is None

    def test_midpoint_valid(self, fact):
        assert fact.midpoint == fact.end - ((fact.end - fact.start) / 2)

    def test_time_of_day_midpoint_invalid(self):
        fact = Fact(activity=None, start=None)
        assert fact.time_of_day_midpoint == ""

    def test_time_of_day_midpoint_valid(self, fact):
        todm = fact.time_of_day_midpoint
        assert " ◐ " in todm

    def test_time_of_day_humanize_invalid_no_start_no_end(self):
        start = datetime.datetime(2015, 12, 10, 12, 30, 33)
        fact = Fact(activity=None, start=start, end=None)
        assert fact.time_of_day_humanize() == ""

    @freeze_time("2015-12-10 18:07")
    def test_time_of_day_humanize_invalid_no_start_no_end_show_now(self):
        start = datetime.datetime(2015, 12, 10, 12, 30, 33)
        fact = Fact(activity=None, start=start, end=None)
        todh = fact.time_of_day_humanize(show_now=True)
        assert todh == "Thu 10 Dec 2015 ◐ 12:30 PM — 06:07 PM"

    def test_time_of_day_humanize_momentaneous(self):
        a_moment = datetime.datetime(1974, 5, 22, 8, 24, 18)
        fact = Fact(activity=None, start=a_moment, end=a_moment)
        todh = fact.time_of_day_humanize()
        assert todh == "Wed 22 May 1974 ◐ 08:24 AM"

    def test_time_of_day_humanize_same_day(self):
        start = datetime.datetime(2015, 12, 10, 12, 30, 33)
        end = datetime.datetime(2015, 12, 10, 13, 30, 33)
        fact = Fact(activity=None, start=start, end=end)
        todh = fact.time_of_day_humanize()
        assert todh == "Thu 10 Dec 2015 ◐ 12:30 PM — 01:30 PM"

    def test_time_of_day_humanize_separate_days(self):
        start = datetime.datetime(2015, 12, 10, 12, 30, 33)
        end = datetime.datetime(2015, 12, 12, 13, 30, 33)
        fact = Fact(activity=None, start=start, end=end)
        todh = fact.time_of_day_humanize()
        assert todh == "Thu 10 Dec 2015 ◐ 12:30 PM — 01:30 PM Sat 12 Dec 2015"

    # ***

    def test_fact_activity_name_invalid(self, fact):
        fact.activity = None
        assert fact.activity_name == ""

    def test_fact_activity_name_valid(self, fact):
        assert fact.activity_name == fact.activity.name

    def test_fact_category(self, fact):
        assert fact.category is fact.activity.category

    def test_fact_category_name_invalid(self, fact):
        fact.activity = None
        assert fact.category_name == ""

    def test_fact_category_name_valid(self, fact):
        assert fact.category_name == fact.activity.category.name

    # ***

    # (lb): Skipping fact.description* and fact.tag* methods that start
    #       at and follow fact.description() (in the module, as of 2020-06-20)
    #       because I see coverage provided incidentally (from other tests).
    #       (And my goal at this moment is 100% coverage, but not necessarily
    #       from this specific test class.)

    # ***

    def test_oid_actegory_empty_default(self):
        fact = Fact(activity=None, start=None)
        assert fact.oid_actegory() == "@"

    def test_oid_actegory_empty_supplied(self):
        fact = Fact(activity=None, start=None)
        empty_actegory_placeholder = "foo"
        txt = fact.oid_actegory(empty_actegory_placeholder=empty_actegory_placeholder)
        assert txt == empty_actegory_placeholder

    def test_oid_actegory_nameless_activity(self, fact):
        fact.activity.name = ""
        assert fact.oid_actegory() == "@{}".format(fact.category_name)

    def test_oid_actegory_both_named_unshelled(self, fact):
        expected = "{}@{}".format(fact.activity_name, fact.category_name)
        assert fact.oid_actegory() == expected

    def test_oid_actegory_both_named_shellify(self, fact):
        expected = '"{}@{}"'.format(fact.activity_name, fact.category_name)
        assert fact.oid_actegory(shellify=True) == expected

    # ***

    def test_oid_description_cut_width(self, fact):
        fact.description = "abc de fghijkl"
        txt = fact.oid_description(cut_width=9, sep=", ")
        assert txt == ", abc de..."

    # ***

    def test_oid_tags_quote_tokens(self, fact):
        txt = fact.oid_tags(quote_tokens=True)
        assert txt.startswith('"#')

    # ***

    def test_friendly_str_basic(self, fact):
        txt = fact.friendly_str()
        assert txt

    def test_friendly_str_localize_True(self, fact):
        Fact.localize(localize=True)
        txt = fact.friendly_str()
        Fact.localize(localize=False)
        # (lb): Being lazy. This test provides coverage, does not check
        # that the start and end time are localized.
        assert txt

    def test_friendly_str_include_id(self, fact):
        txt = fact.friendly_str(include_id=True)
        assert fact.pk is None
        assert txt.startswith("(🏭 None) ")

    def test_friendly_str_cut_width(self):
        start = datetime.datetime(2015, 12, 10, 12, 30, 33)
        fact = Fact(activity=None, start=start, end=None)
        txt = fact.friendly_str(cut_width_complete=16)
        assert txt == "at 2015-12-10..."

    def test_friendly_str_show_elapsed(self, fact):
        txt = fact.friendly_str(show_elapsed=True)
        # (lb): Being lazy. This test provides coverage, does not check
        # for the elapsed time, e.g., ' [3.00 hours] ' in txt.
        assert txt

    # ***

    def test_fact_short(self, fact):
        assert fact.short

    # ***

    def test_create_from_parsed_fact_no_activity_raises(self, fact):
        parsed_fact = {
            "start": fact.start,
            "end": fact.end,
            "activity": None,
        }
        with pytest.raises(ValueError):
            Fact.create_from_parsed_fact(parsed_fact)

    # ***

    def test__str__(self, fact):
        expect_f = "{start} to {end} {activity}@{category}: {tags}: {description}"
        expectation = expect_f.format(
            start=fact.start.strftime("%Y-%m-%d %H:%M:%S"),
            end=fact.end.strftime("%Y-%m-%d %H:%M:%S"),
            activity=fact.activity.name,
            category=fact.category.name,
            tags=fact.tagnames(),
            description=fact.description,
        )
        assert str(fact) == expectation

    def test__str__no_end(self, fact):
        fact.end = None
        expect_f = "at {start} {activity}@{category}: {tags}: {description}"
        expectation = expect_f.format(
            start=fact.start.strftime("%Y-%m-%d %H:%M:%S"),
            activity=fact.activity.name,
            category=fact.category.name,
            tags=fact.tagnames(),
            description=fact.description,
        )
        assert str(fact) == expectation

    def test__str__no_start_no_end(self, fact):
        fact.start = None
        fact.end = None
        expectation = "{activity}@{category}: {tags}: {description}".format(
            activity=fact.activity.name,
            category=fact.category.name,
            tags=fact.tagnames(),
            description=fact.description,
        )
        assert str(fact) == expectation

    # (lb): It might be nice to do snapshot testing. However, that won't
    # work unless we disable the random string generator we use to make up
    # item names.
    #
    # Here's what a snapshot test might look like:
    #
    #   def test__repr__snapshot(self, snapshot, fact):
    #       """
    #       Test repr() against snapshot. Save time not writing test expectation.
    #       """
    #       result = repr(fact)
    #       snapshot.assert_match(result)
    #
    # In lieu of that, we re-generate the repr() herein. Which makes me
    # feel weird, like we're just duplicating what Fact.__repr__ already
    # does.

    def assert_fact_repr(self, the_fact):
        # (lb): I feel somewhat dirty with the test__repr__ methods.
        #   I feel like these should be snapshot tests, and not tests
        #   that require manual labor to maintain a tedious string
        #   builder that basically mimics the behavior of the methods
        #   that we're testing. Blech.
        tag_parts = []
        for tag in the_fact.tags:
            tag_parts.append(TestTag.as_repr(tag))
        tags = ", ".join(tag_parts)
        expect_f = (
            "Fact("
            "_description={description}, "
            "_end={end}, "
            "_start={start}, "
            "activity={activity}, "
            "deleted={deleted}, "
            "pk={pk}, "
            "split_from={split_from}, "
            "tags=[{tags}]"
            ")"
        )
        expectation = expect_f.format(
            pk=repr(the_fact.pk),
            split_from=repr(the_fact.split_from),
            start=repr(the_fact.start),
            end=repr(the_fact.end),
            activity=TestActivity.as_repr(the_fact.activity),
            tags=tags,
            description=repr(the_fact.description),
            deleted=repr(the_fact.deleted),
        )
        result = repr(the_fact)
        assert isinstance(result, str)
        assert result == expectation

    def test__repr__(self, fact):
        """Make sure our debugging representation matches our expectations."""
        self.assert_fact_repr(fact)

    def test__repr__no_end(self, fact):
        """Test that facts without end datetime are represented properly."""
        result = repr(fact)
        assert isinstance(result, str)
        fact.end = None
        self.assert_fact_repr(fact)

    def test__repr__no_start_no_end(self, fact):
        """Test that facts without times are represented properly."""
        fact.start = None
        fact.end = None
        self.assert_fact_repr(fact)

    def test__str__no_tags(self, fact):
        fact.tags = []
        self.assert_fact_repr(fact)
