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

import json


class TestJSONWriter(object):
    """Make sure the JSON writer works as expected."""

    def test_json_writer_write_facts(self, json_writer, list_of_facts):
        """Make sure the calendar is actually written do disk before file is closed."""
        number_of_facts = 5
        facts = list_of_facts(number_of_facts)
        output_path = json_writer.output_file.name
        json_writer.write_facts(facts)
        with open(output_path, "r") as fobj:
            result = json.load(fobj)
            for idx, fact in enumerate(facts):
                assert result[idx] == json_writer.fact_as_dict(fact)

    def test_json_writer_write_report(self, json_writer, fact, table, headers):
        """Make sure the calendar is actually written do disk before file is closed."""
        output_path = json_writer.output_file.name
        json_writer.write_report(table, headers)
        with open(output_path, "r") as fobj:
            result = json.load(fobj)
            for idx, row in enumerate(table):
                kvals = {key: value for key, value in zip(headers, row)}
                assert result[idx] == kvals
