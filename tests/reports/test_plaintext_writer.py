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

import csv
from gettext import gettext as _

import pytest


class TestPlaintextWriter(object):
    def test_plaintext_writer_init(self, plaintext_writer):
        """Make sure that initialition provides us with a ``csv.writer`` instance."""
        assert plaintext_writer.csv_writer
        assert plaintext_writer.csv_writer.dialect == csv.get_dialect("excel")

    def test_plaintext_writer_headers(self, path, plaintext_writer):
        """Make sure that initialition writes header as expected."""
        expectations = (
            "Start time",
            "End time",
            "Duration",
            "Activity",
            "Category",
            "Description",
            "Deleted",
        )
        plaintext_writer.write_facts(facts=[])
        with open(plaintext_writer.output_file.name, "r") as fobj:
            reader = csv.reader(fobj, dialect="excel")
            header = next(reader)
        for field, expectation in zip(header, expectations):
            if isinstance(field, str):
                assert field == expectation
            else:
                assert field.decode("utf-8") == expectation

    def test_plaintext_writer_fact_as_tuple_no_category(self, plaintext_writer, fact):
        """Make sure that ``None`` category values translate to ``empty strings``."""
        fact.activity.category = None
        result = plaintext_writer.fact_as_tuple(fact)
        cat_idx = plaintext_writer.facts_headers().index(_("Category"))
        assert result[cat_idx] == ""

    def test_plaintext_writer_fact_as_tuple_with_category(self, plaintext_writer, fact):
        """Make sure that category references translate to their names."""
        result = plaintext_writer.fact_as_tuple(fact)
        cat_idx = plaintext_writer.facts_headers().index(_("Category"))
        assert result[cat_idx] == fact.category.name

    def test_plaintext_writer__write_fact(self, fact, plaintext_writer):
        """Make sure the writen fact is what we expect."""
        fact_tuple = plaintext_writer.fact_as_tuple(fact)
        plaintext_writer._write_fact(idx=0, fact=fact)
        plaintext_writer._close()
        with open(plaintext_writer.output_file.name, "r", encoding="utf8") as fobj:
            reader = csv.reader(fobj, dialect=plaintext_writer.dialect)
            # If we had called write_facts, would need to ignore headers,
            # e.g.,
            #   next(reader)
            # and then fetch the line.
            line = next(reader)
            for field, expectation in zip(line, fact_tuple):
                if isinstance(field, str):
                    assert field == expectation
                else:
                    assert field.decode("utf-8") == expectation

    def test_plaintext_writer_write_report(self, plaintext_writer, table, headers):
        plaintext_writer.write_report(table, headers)
        with open(plaintext_writer.output_file.name, "r") as fobj:
            reader = csv.reader(fobj, dialect=plaintext_writer.dialect)
            # The first line is the headers.
            csv_headers = next(reader)
            assert csv_headers == headers
            # Remaining lines are data rows.
            for row in table:
                assert row == next(reader)
            with pytest.raises(StopIteration):
                next(reader)
