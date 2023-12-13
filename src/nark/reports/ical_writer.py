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

"""ICAL writer output format module."""

import datetime

import lazy_import

from . import ReportWriter

__all__ = (
    'ICALWriter',
)

# Profiling: load icalendar: ~ 0.008 secs.
icalendar = lazy_import.lazy_module('icalendar')


class ICALWriter(ReportWriter):
    """A simple ical writer for fact export."""
    def __init__(self, *args, **kwargs):
        """
        Initiate new instance and open an output file like object.

        Args:
            path: File like object to be opend. This is where all output
                will be directed to. datetime_format (str): String specifying
                how datetime information is to be rendered in the output.
        """
        kwargs['output_b'] = True
        super(ICALWriter, self).__init__(*args, **kwargs)
        self.calendar = icalendar.Calendar()

    def _write_fact(self, idx, fact):
        """
        Write a singular fact to our report.

        Note:
            * ``dtend`` is non-inclusive according to Page 54 of RFC 5545

        Returns:
            None: If everything worked out alright.
        """
        # [FIXME]
        # It apears that date/time requirements for VEVENT have changed between
        # RFCs. 5545 now seems to require a 'dstamp' and a 'uid'!

        # (lb): I'm not sure the utility of this export format without
        # ever personally having tested importing it anywhere. For
        # instance, maybe exporting the Activity@Category is a better
        # idea than using the separate "categories" and "summary" fields
        # (and I'm not sure how those fields are intended to be used, nor
        # how different applications might show their values). In any case,
        # I've maintained this format because it existed in hamster-lib, and
        # it seems like something people might want.

        event = icalendar.Event()

        event.add('dtstart', fact.start)
        if fact.end:
            # MAGIC_NUMBER: (lb): Add one second, because `dtend` is non-inclusive.
            event.add('dtend', fact.end + datetime.timedelta(seconds=1))
        event.add('categories', [fact.category_name])
        event.add('summary', fact.activity_name)
        event.add('description', fact.description_or_empty)

        self.calendar.add_component(event)

    def write_report(self, table, headers, tabulation=None):
        raise NotImplementedError

    def _close(self):
        """Custom close method to make sure the calendar is actually writen do disk."""
        self.output_file.write(self.calendar.to_ical())
        return super(ICALWriter, self)._close()

