# This file exists within 'nark':
#
#   https://github.com/tallybark/nark
#
# Copyright © 2018-2020 Landon Bouma
# Copyright © 2015-2016 Eric Goller
# All rights reserved.
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

"""nark export reporter base output format class.

- Each output class will support either or both write_facts() and write_report().
"""

import sys

__all__ = (
    'ReportWriter',
)


class ReportWriter(object):
    def __init__(
        self,
        output_b=False,
    ):
        """
        Initiate new instance and open an output file like object.

        Note:
            If you need added bells and wristels (like heading etc.) this would
            probably the method to extend.

        Args:
            path: File-like object or string of path to be opened.

            datetime_format (str): String (sent to strftime) specifying how datetime
                values (Fact start and end) are presented in the output.

            output_b: Whether to open the ``path`` for binary output.
        """
        self.output_b = output_b

    # ***

    def output_setup(
        self,
        output_obj,
        row_limit=0,
        datetime_format=None,
        duration_fmt=None,
    ):
        self.output_file = self.open_output_file(output_obj, self.output_b)

        self.row_limit = row_limit or 0

        self.datetime_format = datetime_format
        if self.datetime_format is None:
            self.datetime_format = '%Y-%m-%d %H:%M:%S'

        self.duration_fmt = duration_fmt
        if self.duration_fmt is None:
            self.duration_fmt = '%H:%M'

    def open_output_file(self, output_obj, output_b=False):
        # FIXME/2020-06-02: Revisit output_b=True, may be different in py3,
        # per these hamster-lib comments:
        #
        #   # No matter through what loops we jump, at the end of the day py27
        #   # ``writerow`` will insist on casting our data to binary str()
        #   # instances. This clearly conflicts with any generic open() that provides
        #   # transparent text input/output and would take care of the encoding
        #   # instead.
        #
        #   # [FIXME]
        #   # If it turns out that this is specific to csv handling we may move it
        #   # there and use a simpler default behaviour for our base method.
        self.output_ours = False
        if not output_obj:
            return sys.stdout
        elif not isinstance(output_obj, str):
            return output_obj
        return self.open_file(output_obj, output_b)

    def open_file(self, path, output_b=False, newline=None):
        self.output_ours = True
        if not output_b:
            return open(path, 'w', encoding='utf-8', newline=newline)
        return open(path, 'wb')

    # ***

    def write_facts(self, facts):
        """
        Write facts to output file and close the file like object.

        Args:
            facts (Iterable): Iterable of ``nark.Fact`` instances to export.

        Returns:
            None: If everything worked as expected.
        """
        n_written = self.write_facts_list(facts)
        self._close()
        return n_written

    def write_facts_list(self, facts):
        """Write facts to output file."""
        n_written = 0
        for idx, fact in enumerate(facts):
            self._write_fact(idx, fact)
            n_written += 1
            if self.row_limit > 0 and n_written >= self.row_limit:
                break
        return n_written

    def _write_fact(self, idx, fact):
        """
        Represent one ``Fact`` in the output file.

        What this means exactly depends on the format and kind of output.

        Args:
            fact (Fact): The Fact to be written.

        Returns:
            None
        """
        raise NotImplementedError

    # ***

    @property
    def requires_table(self):
        return False

    def write_report(self, table, headers, tabulation=None):
        """
        Write report to output file and close the file like object.

        Args:
            facts (Iterable): Iterable of ``nark.Fact`` instances to export.

        Returns:
            None: If everything worked as expected.
        """
        n_written = self.write_report_table(table, headers, tabulation)
        self._close()
        return n_written

    def write_report_table(self, table, headers, tabulation=None):
        """Write report to output file."""
        n_written = 0
        for row in table:
            self._write_result(row, headers, tabulation)
            n_written += 1
            if self.row_limit > 0 and n_written >= self.row_limit:
                break
        return n_written

    def _write_result(self, row, headers, tabulation=None):
        """
        Represent one ``Fact`` or aggregate result in the output file.

        What this means exactly depends on the format and kind of output
        and search paramaters.

        Args:
            fact (Fact): The Fact to be written.

        Returns:
            None
        """
        raise NotImplementedError

    # ***

    def _close(self):
        """Default teardown method."""
        if self.output_ours:
            self.output_file.close()
        # Rather than clear the file handle, leave set, so caller can inspect.
        #  self.output_file = None

# ***

