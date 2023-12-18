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

"""Test for report writer module."""

import os.path
import sys

import pytest

from nark.reports import ReportWriter


class TestReportWriter(object):
    @pytest.mark.parametrize(
        ["datetime_format", "expected_format"],
        [
            [None, "%Y-%m-%d %H:%M:%S"],
            ["%Y-%m-%d", "%Y-%m-%d"],
        ],
    )
    def test_report_writer_init_stores_datetime_format(
        self,
        path,
        datetime_format,
        expected_format,
    ):
        """Make sure that Writer initialization stores the ``datetime_format``."""
        report_writer = ReportWriter()
        report_writer.output_setup(path, datetime_format=datetime_format)
        assert report_writer.datetime_format == expected_format

    def test_report_writer_output_setup_opens_file_path_given(self, path):
        """Make sure a file like object is beeing opened."""
        report_writer = ReportWriter()
        report_writer.output_setup(path)
        assert os.path.isfile(path)
        assert report_writer.output_file.closed is False

    def test_report_writer_output_setup_falls_back_to_stdout(self):
        """Make sure stdout used if no file path specified."""
        report_writer = ReportWriter()
        report_writer.output_setup(output_obj="")
        assert report_writer.output_file is sys.stdout

    def test_report_writer_output_setup_opens_binarily(self, path):
        """Make sure a file is opened for binary when specified."""
        # 2020-06-08: output_b was only used for Python 2 xml, but py2 support
        # long since dropped, so this is the only code that uses output_b.
        report_writer = ReportWriter(output_b=True)
        report_writer.output_setup(path)
        assert report_writer.output_file.mode == "wb"

    def test_report_writer_output_setup_uses_object_pass(self):
        """Make sure stdout used if no file path specified."""
        report_writer = ReportWriter()
        not_a_string_path = object()
        report_writer.output_setup(output_obj=not_a_string_path)
        assert report_writer.output_file is not_a_string_path

    def test_report_writer_write_facts_calls__write_fact(
        self,
        mocker,
        report_writer,
        list_of_facts,
    ):
        """Make sure that each ``Fact`` instances triggers a new line."""
        number_of_facts = 10
        facts = list_of_facts(number_of_facts)
        mocker.patch.object(report_writer, "_write_fact", return_value=None)
        report_writer.write_facts(facts)
        assert report_writer._write_fact.call_count == number_of_facts
        # For coverage!
        assert report_writer.requires_table is False

    def test_report_writer_write_facts_respects_row_limit(
        self,
        mocker,
        report_writer,
        list_of_facts,
    ):
        """Ensure that write_facts respects the row_limit."""
        row_limit = 3
        number_of_facts = 10
        facts = list_of_facts(number_of_facts)
        report_writer.row_limit = row_limit
        mocker.patch.object(report_writer, "_write_fact", return_value=None)
        report_writer.write_facts(facts)
        assert report_writer._write_fact.call_count == row_limit

    def test_report_writer_write_facts_fails_to__close(
        self,
        report_writer,
        list_of_facts,
    ):
        """Make sure our output file is closed at the end."""
        number_of_facts = 10
        facts = list_of_facts(number_of_facts)
        assert report_writer.output_file.closed is False
        # Because we do not mock _write_fact, it raises.
        with pytest.raises(NotImplementedError):
            report_writer.write_facts(facts)
        assert report_writer.output_file.closed is False

    def test_report_writer_write_report_calls__write_result(
        self,
        mocker,
        report_writer,
        table,
        headers,
    ):
        mocker.patch.object(report_writer, "_write_result", return_value=None)
        report_writer.write_report(table, headers)
        assert report_writer._write_result.call_count == len(table)

    def test_report_writer_write_report_respects_row_limit(
        self,
        mocker,
        report_writer,
        table,
        headers,
    ):
        """Ensure that write_report respects the row_limit."""
        row_limit = 3
        report_writer.row_limit = row_limit
        mocker.patch.object(report_writer, "_write_result", return_value=None)
        report_writer.write_report(table, headers)
        assert report_writer._write_result.call_count == row_limit

    def test_report_writer_write_report_fails_to__close(
        self,
        report_writer,
        table,
        headers,
    ):
        assert report_writer.output_file.closed is False
        # Because we do not mock _write_result, it raises.
        with pytest.raises(NotImplementedError):
            report_writer.write_report(table, headers)
        assert report_writer.output_file.closed is False

    def test_report_writer__close(self, report_writer, path):
        """Ensure that the the output gets closed."""
        report_writer._close()
        assert report_writer.output_file.closed
