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

"""XML writer output format module."""

import lazy_import

from . import ReportWriter

__all__ = (
    'XMLWriter',
)

# Profiling: load Document: ~ 0.004 secs.
minidom = lazy_import.lazy_module('xml.dom.minidom')


class XMLWriter(ReportWriter):
    """Writer for a basic xml export."""
    # (lb): @elbenfreund noted that XMLWriter copied from 'legacy hamster':
    #   Authored by tstriker <https://github.com/tstriker>. Docstrings by elbenfreund.
    #   https://github.com/projecthamster/hamster/blame/66ed9270c6f0070a4548aca9f070517cc13c85ae
    #       /src/hamster/reports.py#L159
    #   (Other than this class, the nark code authors are either:
    #    landonb (2018-2020); or elbenfreund (2015-2017).)

    def __init__(self, *args, **kwargs):
        """Setup the writer including a main xml document."""
        kwargs['output_b'] = True
        super(XMLWriter, self).__init__(*args, **kwargs)

    def start_document(self, element_name):
        # Profiling: load Document: ~ 0.004 secs.
        self.document = minidom.Document()
        self.fact_list = self.document.createElement(element_name)

    def write_facts(self, facts):
        self.start_document('facts')
        return super(XMLWriter, self).write_facts(facts)

    def _write_fact(self, idx, fact):
        """
        Create new fact element and populate attributes.

        Once the child is prepared append it to ``fact_list``.
        """
        elem = self.document.createElement("fact")
        elem.setAttribute('start', fact.start_fmt(self.datetime_format))
        elem.setAttribute('end', fact.end_fmt(self.datetime_format))
        elem.setAttribute('activity', fact.activity_name)
        elem.setAttribute('duration', fact.format_delta(style=self.duration_fmt))
        elem.setAttribute('category', fact.category_name)
        elem.setAttribute('description', fact.description_or_empty)
        self.fact_list.appendChild(elem)

    def write_report(self, table, headers, tabulation=None):
        self.start_document('results')
        return super(XMLWriter, self).write_report(table, headers, tabulation)

    def _write_result(self, row, headers, tabulation=None):
        """
        Create new fact element and populate attributes.

        Once the child is prepared append it to ``fact_list``.
        """
        fact = self.document.createElement("fact")
        for idx, header in enumerate(headers):
            fact.setAttribute(header, row[idx])
        self.fact_list.appendChild(fact)

    def _close(self):
        """
        Append the xml fact list to the main document write file and cleanup.

        ``toxml`` should take care of encoding everything with UTF-8.
        """

        self.document.appendChild(self.fact_list)
        self.output_file.write(self.document.toxml(encoding='utf-8'))
        return super(XMLWriter, self)._close()

