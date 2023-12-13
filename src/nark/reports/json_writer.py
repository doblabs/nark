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

"""JSON writer output format module."""

import json

from . import ReportWriter

__all__ = (
    'JSONWriter',
)


class JSONWriter(ReportWriter):
    def __init__(self):
        """Initialize a new JSONWriter instance."""
        super(JSONWriter, self).__init__()

    def fact_as_dict(self, fact):
        kvals = {
            'start': fact.start_fmt(self.datetime_format),
            'end': fact.end_fmt(self.datetime_format),
            'activity': fact.activity_name,
            'duration': fact.format_delta(style=self.duration_fmt),
            'category': fact.category_name,
            'description': fact.description_or_empty,
        }
        return kvals

    def init_result_list(self):
        self.result_list = []

    def write_result_list(self):
        json.dump(self.result_list, self.output_file)
        n_written = len(self.result_list)
        del self.result_list
        return n_written

    def write_facts_list(self, facts):
        self.init_result_list()
        super(JSONWriter, self).write_facts_list(facts)
        n_written = self.write_result_list()
        return n_written

    def _write_fact(self, idx, fact):
        kvals = self.fact_as_dict(fact)
        self.result_list.append(kvals)

    def write_report_table(self, table, headers, tabulation=None):
        self.init_result_list()
        super(JSONWriter, self).write_report_table(table, headers, tabulation)
        n_written = self.write_result_list()
        return n_written

    def _write_result(self, row, headers, tabulation=None):
        kvals = {header: value for header, value in zip(headers, row)}
        self.result_list.append(kvals)

