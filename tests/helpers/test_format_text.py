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

from nark.helpers.format_text import format_value_truncate


class TestFormatText(object):
    def test_format_value_truncate_one_word(self):
        truncated = format_value_truncate("abcdefghijkl", trunc_width=6)
        assert truncated == "..."

    def test_format_value_truncate_two_words(self):
        truncated = format_value_truncate("abc defghijkl", trunc_width=9)
        assert truncated == "abc..."

    def test_format_value_truncate_abc_de_6_plain(self):
        truncated = format_value_truncate(
            "abc de fghijkl",
            trunc_width=9,
        )
        assert truncated == "abc de..."

    def test_format_value_truncate_abc_de_6_italic_reset(self):
        truncated = format_value_truncate(
            "\x1b[3mabc de fghijkl\x1b[0m",
            trunc_width=9,
        )
        assert truncated == "\x1b[3mabc de...\x1b[0m"
