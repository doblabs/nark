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

from nark.reports import ReportWriter
from nark.reports.csv_writer import CSVWriter
from nark.reports.ical_writer import ICALWriter
from nark.reports.json_writer import JSONWriter
from nark.reports.plaintext_writer import PlaintextWriter
from nark.reports.tsv_writer import TSVWriter
from nark.reports.xml_writer import XMLWriter

# Register the fact_factory, etc.
from nark.tests.item_factories import *  # noqa: F401, F403


@pytest.fixture
def path(tmpdir):
    path = tmpdir.mkdir("reports").join("export.fmt").strpath
    return path


@pytest.fixture
def report_writer(path):
    report_writer = ReportWriter()
    report_writer.output_setup(path)
    return report_writer


@pytest.fixture
def csv_writer(path):
    csv_writer = CSVWriter()
    csv_writer.output_setup(path)
    return csv_writer


@pytest.fixture
def ical_writer(path):
    ical_writer = ICALWriter()
    ical_writer.output_setup(path)
    return ical_writer


@pytest.fixture
def json_writer(path):
    json_writer = JSONWriter()
    json_writer.output_setup(path)
    return json_writer


@pytest.fixture
def plaintext_writer(path):
    plaintext_writer = PlaintextWriter()
    plaintext_writer.output_setup(path)
    return plaintext_writer


@pytest.fixture
def tsv_writer(path):
    tsv_writer = TSVWriter()
    tsv_writer.output_setup(path)
    return tsv_writer


@pytest.fixture
def xml_writer(path):
    xml_writer = XMLWriter()
    xml_writer.output_setup(path)
    return xml_writer


# ***


@pytest.fixture
def list_of_facts(fact_factory):
    """
    Provide a factory that returns a list with given amount of Fact instances.

    The key point here is that these fact *do not overlap*!
    """

    def get_list_of_facts(number_of_facts):
        facts = []
        # MAYBE: Use controller.store.now ?
        old_start = datetime.datetime.utcnow().replace(microsecond=0)
        offset = datetime.timedelta(hours=4)
        for i in range(number_of_facts):
            start = old_start + offset
            facts.append(fact_factory(start=start))
            old_start = start
        return facts

    return get_list_of_facts


# ***

FAKER_WORDS_NB = 6

FAKER_TABLE_LEN = 3


@pytest.fixture
def headers(faker):
    return faker.words(nb=FAKER_WORDS_NB)


@pytest.fixture
def row(faker):
    return faker.words(nb=FAKER_WORDS_NB)


@pytest.fixture
def table(faker):
    table = []
    for iters in range(FAKER_TABLE_LEN):
        table.append(faker.words(nb=FAKER_WORDS_NB))
    return table
