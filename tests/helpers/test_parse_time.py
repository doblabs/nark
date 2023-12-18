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

from nark.helpers import fact_time
from nark.helpers.parse_errors import ParserInvalidDatetimeException
from nark.helpers.parse_time import HamsterTimeSpec, parse_dated, parse_datetime_human


class TestGetDayEnd(object):
    @pytest.mark.parametrize(
        ("day_start", "expectation"),
        [
            (datetime.time(0, 0, 0), datetime.time(23, 59, 59)),
            (datetime.time(5, 30, 0), datetime.time(5, 29, 59)),
            (datetime.time(23, 59, 59), datetime.time(23, 59, 58)),
            (datetime.time(14, 44, 23), datetime.time(14, 44, 22)),
        ],
    )
    def test_various_day_start_times(self, base_config, day_start, expectation):
        """Ensure that resulting end times match our expectation given ``day_start``-"""
        base_config["time.day_start"] = day_start
        assert fact_time.day_end_time(day_start) == expectation


class TestEndDayToDatetime(object):
    @pytest.mark.parametrize(
        ("day_start", "expectation"),
        [
            (datetime.time(0, 0, 0), datetime.datetime(2015, 4, 15, 23, 59, 59)),
            (datetime.time(5, 30, 0), datetime.datetime(2015, 4, 16, 5, 29, 59)),
            (datetime.time(23, 59, 59), datetime.datetime(2015, 4, 16, 23, 59, 58)),
            (datetime.time(14, 44, 23), datetime.datetime(2015, 4, 16, 14, 44, 22)),
        ],
    )
    def test_same_end_day_various_day_starts(self, day_start, expectation):
        """
        Ensure that resulting ``end datetimes`` match our expectation given ``day_end``
        """
        end_day = datetime.datetime(2015, 4, 15)
        assert fact_time.day_end_datetime(end_day, day_start) == expectation


# ***


class TestParseTimeHamsterTimeSpec(object):
    """Tests the parse_time module's HamsterTimeSpec class."""

    # Note that much of HamsterTimeSpec indirectly tested via test_parsing.py.

    def test_cannot_instantiate(self):
        with pytest.raises(NotImplementedError):
            HamsterTimeSpec()

    def test_has_time_of_day_false(self):
        has_tod = HamsterTimeSpec.has_time_of_day("2015-12-12")
        assert not has_tod

    def test_has_time_of_day_true(self):
        has_tod = HamsterTimeSpec.has_time_of_day("2015-12-12 18:55")
        assert has_tod


@freeze_time("2015-12-10 12:30")
class TestParseTimeFunctions(object):
    """Tests the parse_time module."""

    # Note that much of parse_time.py indirectly tested via test_parsing.py.

    @pytest.mark.parametrize(
        ("time", "expectation"),
        [
            ("18:55", datetime.datetime(2015, 12, 9, 18, 55)),
            ("18:55:34", datetime.datetime(2015, 12, 9, 18, 55, 34)),
            ("2014-12-10", datetime.datetime(2014, 12, 10, 0, 0)),
            ("2015-10-02 18:12", datetime.datetime(2015, 10, 2, 18, 12)),
            ("2015-10-02 18:12:33", datetime.datetime(2015, 10, 2, 18, 12, 33)),
            # Relative time.
            ("-60", datetime.datetime(2015, 12, 10, 11, 30)),
            ("+2h", datetime.datetime(2015, 12, 10, 14, 30)),
            # Friendly time.
            ("Monday", datetime.datetime(2015, 12, 7, 0, 0)),
        ],
    )
    def test_parse_dated_valid_times(self, time, expectation):
        """Make sure that given times are parsed as expected."""
        parsed = parse_dated(time, time_now=datetime.datetime.now())
        assert parsed == expectation

    @pytest.mark.parametrize(
        "time",
        [
            "18 55",
            "18:555",
            "18:66",
            "2014 01 04 12:30",
            "2014-13-13 12:30",
        ],
    )
    def test_parse_dated_invalid_times(self, time):
        """Ensure that invalid times throw an exception."""
        with pytest.raises(ParserInvalidDatetimeException):
            # F841 local variable 'parsed_' is assigned to but never used
            parsed_ = parse_dated(  # noqa: F841
                time,
                time_now=datetime.datetime.now(),
                cruftless=True,
            )
            assert False  # Unreachable.

    def test_parse_dated_not_a_str(self):
        not_a_str = object()
        parsed = parse_dated(not_a_str, time_now=datetime.datetime.now())
        assert parsed is not_a_str

    def test_parse_datetime_human_local_tz_True(self):
        # FIXME: (lb): There's a timezone feature coming. I swear. One of these years.
        #        For now, can at least test those 2 lines that production does not use.
        # Acceptable time zones, e.g.: '+0500', 'US/Eastern', datetime.timezone.utc.
        # You can also specify tzinfo in datetime.
        parsed = parse_datetime_human(
            "Monday",
            time_now=datetime.datetime.now(),
            local_tz="UTC",
        )
        expected = datetime.datetime(2015, 12, 7, 0, 0, tzinfo=datetime.timezone.utc)
        assert parsed == expected


# ***


class TestValidateStartEndRange(object):
    """Unittests for validation function."""

    @pytest.mark.parametrize(
        "range",
        (
            (
                datetime.datetime(2016, 12, 1, 12, 30),
                datetime.datetime(2016, 12, 1, 12, 45),
            ),
            (
                datetime.datetime(2016, 1, 1, 12, 30),
                datetime.datetime(2016, 12, 1, 12, 45),
            ),
            (
                datetime.datetime(2016, 1, 1, 12, 30),
                datetime.datetime(2016, 12, 1, 1, 45),
            ),
        ),
    )
    def test_valid_ranges(self, range):
        """Make sure that ranges with end > start pass validation."""
        result = fact_time.must_not_start_after_end(range)
        assert result == range

    @pytest.mark.parametrize(
        "range",
        (
            (
                datetime.datetime(2016, 12, 1, 12, 30),
                datetime.datetime(2016, 12, 1, 10, 45),
            ),
            (
                datetime.datetime(2016, 1, 13, 12, 30),
                datetime.datetime(2016, 1, 1, 12, 45),
            ),
        ),
    )
    def test_invalid_ranges(self, range):
        """Make sure that ranges with start > end fail validation."""
        with pytest.raises(ValueError):
            fact_time.must_not_start_after_end(range)
