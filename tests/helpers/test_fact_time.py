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

# Most of nark/helpers/fact_time.py is tested incidentally by other tests.
# (lb): Here I'm just filling in the blanks.

import datetime

import pytest

from nark.helpers.fact_time import (
    datetime_from_clock_after,
    datetime_from_clock_prior,
    day_end_datetime,
    must_be_datetime_or_relative,
    must_not_start_after_end,
    parse_clock_time
)


@pytest.fixture
def clock_time():
    clock_time = '22:59'
    return parse_clock_time(clock_time)


@pytest.fixture
def dt_relative_early():
    dt_relative = datetime.datetime(2015, 12, 10, 12, 30, 0)
    return dt_relative


@pytest.fixture
def dt_relative_later():
    dt_relative = datetime.datetime(2015, 12, 10, 23, 30, 0)
    return dt_relative


class TestFactTime(object):
    def test_datetime_from_clock_prior_day_before(self, dt_relative_early, clock_time):
        new_dt = datetime_from_clock_prior(dt_relative_early, clock_time)
        assert new_dt == datetime.datetime(2015, 12, 9, 22, 59)

    def test_datetime_from_clock_prior_same_day(self, dt_relative_later, clock_time):
        new_dt = datetime_from_clock_prior(dt_relative_later, clock_time)
        assert new_dt == datetime.datetime(2015, 12, 10, 22, 59, 0)

    def test_datetime_from_clock_after_same_day(self, dt_relative_early, clock_time):
        new_dt = datetime_from_clock_after(dt_relative_early, clock_time)
        assert new_dt == datetime.datetime(2015, 12, 10, 22, 59, 0)

    def test_datetime_from_clock_after_day_after(self, dt_relative_later, clock_time):
        new_dt = datetime_from_clock_after(dt_relative_later, clock_time)
        assert new_dt == datetime.datetime(2015, 12, 11, 22, 59, 0)

    def test_day_end_datetime_day_starts_midnight(self, dt_relative_early):
        end = day_end_datetime(end_date=dt_relative_early)
        assert end == datetime.datetime(2015, 12, 10, 23, 59, 59)

    def test_day_end_datetime_day_starts_special(self, dt_relative_early):
        start_time = datetime.time(hour=15, minute=34)
        end = day_end_datetime(dt_relative_early, start_time)
        assert end == datetime.datetime(2015, 12, 11, 15, 33, 59)

    def test_must_be_datetime_or_relative_datetime(self):
        dt = datetime.datetime(2015, 12, 10, 12, 30, 33, 1234)
        new_dt = must_be_datetime_or_relative(dt)
        assert new_dt == datetime.datetime(2015, 12, 10, 12, 30, 33)

    def test_must_be_datetime_or_relative_not_relative_raises(self):
        dt = 'foo'
        with pytest.raises(TypeError) as excinfo:
            must_be_datetime_or_relative(dt)
        errmsg = 'Expected time entry to indicate relative time, not:'
        assert str(excinfo.value).startswith(errmsg)

    def test_must_be_datetime_or_relative_not_relative_valid(self):
        dt = '-5h13m'
        new_dt = must_be_datetime_or_relative(dt)
        assert new_dt == dt

    def test_must_be_datetime_or_relative_not_relative_invalid(self):
        dt = object()
        with pytest.raises(TypeError) as excinfo:
            must_be_datetime_or_relative(dt)
        errmsg = 'Time entry not `datetime`, relative string, or `None`, but:'
        assert str(excinfo.value).startswith(errmsg)

    def test_must_not_start_after_end_start_after_end_raises(
        self, dt_relative_early, dt_relative_later,
    ):
        range_tuple = (dt_relative_later, dt_relative_early)
        with pytest.raises(ValueError) as excinfo:
            must_not_start_after_end(range_tuple)
        errmsg = 'Start after end!'
        assert str(excinfo.value) == errmsg

    def test_must_not_start_after_end_end_after_start_valid(
        self, dt_relative_early, dt_relative_later,
    ):
        range_tuple = (dt_relative_early, dt_relative_later)
        new_rt = must_not_start_after_end(range_tuple)
        assert new_rt == range_tuple

    def test_parse_clock_time_valid(self, clock_time):
        clock_time = '22:59'
        parsed_ct = parse_clock_time(clock_time)
        assert parsed_ct == (22, 59, 0)

    def test_parse_clock_time_invalid(self):
        not_clock_time = '24:99'
        parsed_ct = parse_clock_time(not_clock_time)
        assert parsed_ct is None

