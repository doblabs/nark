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

import xml


class TestXMLWriter(object):
    """Make sure the XML writer works as expected."""

    def test_xml_writer_start_document(self, xml_writer, faker):
        """Make sure a XML main document and a facts list child element is set up."""
        ename = faker.word()
        xml_writer.start_document(ename)
        assert xml_writer.document
        assert xml_writer.fact_list
        assert xml_writer.fact_list.tagName == ename

    def test_xml_writer__write_fact(self, xml_writer, fact, mocker):
        """Make sure that the attributes attached to the fact matche our
        expectations."""
        # (lb): I tried patching the Class method so we could call write_facts, e.g.,
        #   from xml.dom.minidom import Node
        #   mocker.patch.object(Node, 'appendChild')
        #   xml_writer.write_facts([fact])
        # But then the elem.setAttribute() methods do not work.
        # So call _write_fact directly, and test write_facts elsewhere.
        xml_writer.start_document("facts")
        mocker.patch.object(xml_writer.fact_list, "appendChild")
        xml_writer._write_fact(idx=0, fact=fact)
        # Grab the document element created and passed to appendChild.
        result = xml_writer.fact_list.appendChild.call_args[0][0]
        fact_start = fact.start_fmt(xml_writer.datetime_format)
        fact_end = fact.end_fmt(xml_writer.datetime_format)
        fact_duration = fact.format_delta(style=xml_writer.duration_fmt)
        assert result.getAttribute("start") == fact_start
        assert result.getAttribute("end") == fact_end
        assert result.getAttribute("duration") == fact_duration
        assert result.getAttribute("activity") == fact.activity_name
        assert result.getAttribute("category") == fact.category_name
        assert result.getAttribute("description") == fact.description_or_empty

    def test_xml_writer_write_report(self, xml_writer, mocker, headers, row):
        xml_writer.start_document("results")
        mocker.patch.object(xml_writer.fact_list, "appendChild")
        xml_writer._write_result(row, headers)
        result = xml_writer.fact_list.appendChild.call_args[0][0]
        for idx, col in enumerate(headers):
            assert result.getAttribute(col) == row[idx]

    def test_xml_writer_write_facts__close(self, xml_writer, fact, path):
        """Make sure the calendar is actually written do disk before file is closed."""
        xml_writer.write_facts([fact])
        with open(path, "r", encoding="utf8") as fobj:
            result = xml.dom.minidom.parse(fobj)
            assert result.toxml()

    def test_xml_writer_write_report__close(self, xml_writer, table, headers):
        """Make sure the calendar is actually written do disk before file is closed."""
        output_path = xml_writer.output_file.name
        xml_writer.write_report(table, headers)
        with open(output_path, "r") as fobj:
            result = xml.dom.minidom.parse(fobj)
            assert result.toxml()
