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
from icalendar import Calendar


class TestICALWriter(object):
    """Make sure the iCal writer works as expected."""

    def test_ical_writer_init(self, ical_writer):
        """Make sure that init creates a new calendar instance to add events to."""
        assert ical_writer.calendar

    def test_ical_writer_write_facts_expected(self, ical_writer, fact, mocker):
        """Make sure that the fact attached to the calendar matches our expectations."""
        mocker.patch.object(ical_writer.calendar, "add_component")
        ical_writer.write_facts([fact])
        # Retrieve the generated icalendar.Event.
        result = ical_writer.calendar.add_component.call_args[0][0]
        assert result.get("dtstart").dt == fact.start
        assert result.get("dtend").dt == fact.end + datetime.timedelta(seconds=1)
        assert result.get("summary") == fact.activity_name
        # Make lists of [vText] and [str], else comparison fails.
        #  NO: assert result.get('categories') == fact.category
        assert list(result.get("categories").cats) == list([fact.category_name])
        assert result.get("categories").cats[0] == fact.category_name
        assert result.get("description") == fact.description_or_empty

    def test_ical_writer_write_report_not_implemented(self, ical_writer):
        with pytest.raises(NotImplementedError):
            ical_writer.write_report(table=[], headers=[])

    def test_ical_writer_write_facts_written(self, ical_writer, fact, path):
        """Make sure the calendar is actually written to disk before file is closed."""
        ical_writer.write_facts([fact])
        with open(path, "r") as fobj:
            # Create an icalendar.cal.Calendar from the file contents.
            result = Calendar.from_ical(fobj.read())
            assert result.walk()
