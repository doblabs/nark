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

import re

from nark import get_version


class TestNarkGetVer:
    def test_get_version_argless(self):
        # E.g., '3.2.4.dev5+gd15b68dc.d20201209'
        pkg_version = get_version()
        assert re.match(r"^[0-9]+\.[0-9]+", pkg_version)

    def test_get_version_include_head_normal(self):
        # E.g., '3.2.4.dev5+gd15b68dc.d20201209 (3.2.4.dev16+g2bd6b40e)'
        pkg_version = get_version(include_head=True)
        assert re.match(r"^[0-9]+\.[0-9]+.* (.*)$", pkg_version)
