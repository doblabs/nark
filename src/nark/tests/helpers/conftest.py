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

"""Fixtures to help test nark.helpers and related."""

import datetime

# CAVEAT: Note that freeze_time expected to be used with this!
#  @freeze_time('2015-12-25 18:00')
factoid_fixture = (
    ("raw_fact", "time_hint", "expectation"),
    [
        # Use clock-to-clock format, the date inferred from now; with actegory.
        (
            "13:00 to 16:30: foo@bar",
            "verify_both",
            {
                "start_raw": "13:00",
                "end_raw": "16:30",
                "start": datetime.datetime(2015, 12, 25, 13, 0, 0),
                "end": datetime.datetime(2015, 12, 25, 16, 30, 0),
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # *** Test the '-' and ' - ' separators.
        # Use clock-to-clock without spaces format.
        (
            "13:00-16:30: foo@bar",
            "verify_both",
            {
                "start_raw": "13:00",
                "end_raw": "16:30",
                "start": datetime.datetime(2015, 12, 25, 13, 0, 0),
                "end": datetime.datetime(2015, 12, 25, 16, 30, 0),
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # Test wrap-around relative clock times specified.
        (
            "12:00:11 - 11:01:59: act @",
            "verify_both",
            {
                "start_raw": "12:00:11",
                "end_raw": "11:01:59",
                "start": datetime.datetime(2015, 12, 25, 12, 0, 11),
                "end": datetime.datetime(2015, 12, 26, 11, 1, 59),
                "activity": "act",
                "category": "",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # MAYBE/2020-07-03: Note that "clock-clock" works (no spaces around dash)
        # but that "friendly-clock", "clock-friendly", etc., does not.
        # - For consistency, perhaps this should be fixed... or at least documented
        #   that it doesn't.
        (
            "Monday-13:00: foo@bar",
            "verify_both",
            {
                "err": "Expected to find the two datetimes separated by one of: ",
            },
        ),
        (
            "Monday - 13:00: foo@bar",
            "verify_both",
            {
                "start_raw": datetime.datetime(2015, 12, 21, 0, 0, 0),
                "end_raw": "13:00",
                "start": datetime.datetime(2015, 12, 21, 0, 0, 0),
                "end": datetime.datetime(2015, 12, 21, 13, 0, 0),
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # ***
        # Use datetime-to-datetime format, with actegory.
        (
            "2015-12-12 13:00 to 2015-12-12 16:30: foo@bar",
            "verify_both",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": datetime.datetime(2015, 12, 12, 16, 30, 0),
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": datetime.datetime(2015, 12, 12, 16, 30, 0),
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # The end date is inferred from start date.
        (
            "2015-12-12 13:00 - 18:00 foo@bar",
            "verify_both",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": "18:00",
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": datetime.datetime(2015, 12, 12, 18, 00, 0),
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # actegory spanning day (straddles) midnight) and spanning multiple days.
        (
            "2015-12-12 13:00 - 2015-12-25 18:00 foo@bar",
            "verify_both",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": datetime.datetime(2015, 12, 25, 18, 00, 0),
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": datetime.datetime(2015, 12, 25, 18, 00, 0),
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # Create open/ongoing/un-ended fact.
        (
            "2015-12-12 13:00 foo@bar",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # - LOST_IT: (lb): I had a note suggesting this test tickles that unlikely path
        #   with start=None (in must_create_fact_from_factoid, or mend_fact_timey_wimey,
        #   or Fact.create_from_factoid), but I cannot find that branch, nor does this
        #   test tickle any affirm(False)... but not deleting this comment, because I'm
        #   still suspicious.
        # Create ongoing fact starting at right now.
        (
            "foo@bar",
            "verify_none",
            {
                "start_raw": None,
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # Similar to previous, but avoid re-raising ParserMissingDatetimeOneException
        # (and grabs us one more line of coverage, the `if minmax[0] == 0` branch).
        (
            "foo@bar",
            "verify_then",
            {
                "start_raw": None,
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        (
            "foo@bar",
            "verify_still",
            {
                "start_raw": None,
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # ***Test verify_both's `strictly_two` branches.
        # Test the first branch:
        #   elif strictly_two:
        #       self.raise_missing_datetime_two()
        (
            "2015-12-12 13:00 foo@bar",
            "verify_both",
            {
                "err": "Expected to find the two datetimes separated by one of: ",
            },
        ),
        # Test the second branch of same, immediately following previous.
        (
            "2015-12-12 13:00: foo@bar",
            "verify_both",
            {
                "err": "Expected to find the two datetimes separated by one of: ",
            },
        ),
        # *** Test tags.
        # 2 Simple Tags.
        (
            "2015-12-12 13:00 foo@bar: #precious #hashish, i like ike",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": ["precious", "hashish"],
                "description": "i like ike",
                "warnings": [],
            },
        ),
        # Multiple Tags are identified by a clean leading delimiter character.
        (
            '2015-12-12 13:00 foo@bar, #just walk away "#not a tag", blah',
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": ['just walk away "#not a tag"'],
                "description": "blah",
                "warnings": [],
            },
        ),
        # Alternative tag delimiter; and quotes are just consumed as part of tag.
        (
            '2015-12-12 13:00 foo@bar, #just walk away @"totes a tag", blah',
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": ["just walk away", '"totes a tag"'],
                "description": "blah",
                "warnings": [],
            },
        ),
        # Test '#' in description, elsewhere, after command, etc.
        (
            '2015-12-12 13:00 baz@bat",'
            " #tag1, #tag2 tags cannot come #too late, aha!"
            " Time is also ignored at end: 12:59",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": None,
                "activity": "baz",
                "category": 'bat"',
                "tags": ["tag1"],
                "description": "#tag2 tags cannot come #too late, aha!"
                " Time is also ignored at end: 12:59",
                "warnings": [],
            },
        ),
        # ***
        # No tags, just description, tests Parser.RE_SPLIT_CAT_AND_TAGS.match
        # returns None.
        (
            "2015-12-12 13:00 foo@bar: blah blah blah",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "blah blah blah",
                "warnings": [],
            },
        ),
        # No act@cat but tags and description, tests `parse_tags_and_remainder`
        # self.re_item_sep.match branch.
        (
            "2015-12-12 13:00: #baz: bat",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "end": None,
                "activity": "",
                "category": "",
                "tags": ["baz"],
                "description": "bat",
                "warnings": [],
            },
        ),
        # (lb): This one... may or may be making the best decision:
        # what looks like a tag is being gobbled as the description.
        (
            "foo@bar #baz",
            "verify_none",
            {
                "start_raw": None,
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "#baz",
                "warnings": [],
            },
        ),
        # (lb): Similar to previous example, this might not be what user
        # would except, but adding a separator (colon) does signal intent,
        # so this one feels like it does behave the way it should.
        (
            "foo@bar #baz:",
            "verify_none",
            {
                "start_raw": None,
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar #baz",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        (
            "foo@bar #baz: #bat",
            "verify_none",
            {
                "start_raw": None,
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar #baz",
                "tags": ["bat"],
                "description": "",
                "warnings": [],
            },
        ),
        (
            "foo@bar #baz: bat",
            "verify_none",
            {
                "start_raw": None,
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar #baz",
                "tags": [],
                "description": "bat",
                "warnings": [],
            },
        ),
        (
            "foo@bar #baz: #bat: cat",
            "verify_none",
            {
                "start_raw": None,
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar #baz",
                "tags": ["bat"],
                "description": "cat",
                "warnings": [],
            },
        ),
        # ***
        # Note that dateparser uses current clock time for time relative to
        # now, e.g., 'yesterday', '1 day ago', etc, but it uses midnight for
        # absolute references, e.g., 'Monday', 'January', etc.
        # - The 18:00:00 is in reference to: @freeze_time('2015-12-25 18:00').
        (
            "Monday until 2 days ago: act @",
            "verify_both",
            {
                "start_raw": datetime.datetime(2015, 12, 21, 0, 0, 0),
                "end_raw": datetime.datetime(2015, 12, 23, 18, 0, 0),
                "start": datetime.datetime(2015, 12, 21, 0, 0, 0),
                "end": datetime.datetime(2015, 12, 23, 18, 0, 0),
                "activity": "act",
                "category": "",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # ***
        # Test must_parse_datetimes_known `not self.raw_datetime1` if-branch.
        (
            "-90: foo@bar",
            "verify_end",
            {
                "start_raw": None,
                "end_raw": "-90",
                "start": None,
                "end": datetime.datetime(2015, 12, 25, 16, 30, 0),
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # Note that you should not include the time verb
        # (which is encapsulated in the time_hint).
        (
            "to -90: foo@bar",
            "verify_end",
            {
                "start_raw": None,
                "end_raw": datetime.datetime(1990, 12, 25, 0, 0, 0),
                "start": None,
                "end": datetime.datetime(1990, 12, 25, 0, 0, 0),
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # Test must_parse_datetimes_known `not self.raw_datetime1` else-branch.
        (
            "Monday: foo@bar",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 21, 0, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 21, 0, 0, 0),
                "end": None,
                "activity": "foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # Test warn_if_datetime_missing_clock_time, if looks_like_clock_abbrev.
        (
            "2015-12-12 300 foo@bar",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 0, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 0, 0, 0),
                "end": None,
                "activity": "300 foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [
                    "The identified datetime is missing the time of day. "
                    "Perhaps those three digits after the date "
                    "should be a 4-digit clocktime?"
                ],
                "err": "",
            },
        ),
        # Test warn_if_datetime_missing_clock_time, if not looks_like_clock_abbrev.
        (
            "2015-12-12 9 foo@bar",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 12, 0, 0, 0),
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 12, 0, 0, 0),
                "end": None,
                "activity": "9 foo",
                "category": "bar",
                "tags": [],
                "description": "",
                "warnings": [
                    "The identified datetime is missing the time of day. "
                    "Is that what you wanted? (Probably not!)"
                ],
                "err": "",
            },
        ),
        # Obscure Factoid covers last branch in `must_parse_datetime_from_rest`.
        (
            "+10m to @",
            "verify_start",
            {
                "start_raw": "+10m",
                "end_raw": None,
                "start": datetime.datetime(2015, 12, 25, 18, 0, 0),
                "end": None,
                "activity": "to",
                "category": "",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
        # *** must_parse_datetimes_magic tests.
        # Test `if two_is_okay`-`elif strictly_two` in `must_parse_datetimes_magic`.
        (
            "+10m foo@bar",
            "verify_both",
            {
                "err": "Expected to find the two datetimes separated by one of: ",
            },
        ),
        # Test `if not self.raw_datetime1`-`== 'verify_end'`
        # in `must_parse_datetimes_magic`.
        (
            "Monday foo@bar",
            "verify_end",
            {
                "err": "Expected to find the two datetimes separated by one of: ",
            },
        ),
        # Test `if not self.raw_datetime1`-`!= 'verify_end'`
        # in `must_parse_datetimes_magic`.
        (
            "Monday foo@bar",
            "verify_start",
            {
                "err": "Expected to find a datetime.",
            },
        ),
        # Cover final line in must_parse_datetimes_magic.
        (
            "Tuesday to 12:00 @",
            "verify_start",
            {
                "start_raw": datetime.datetime(2015, 12, 22, 0, 0, 0),
                "end_raw": "12:00",
                "start": datetime.datetime(2015, 12, 22, 0, 0, 0),
                "end": "12:00",
                "activity": "",
                "category": "",
                "tags": [],
                "description": "",
                "warnings": [],
            },
        ),
    ],
)
