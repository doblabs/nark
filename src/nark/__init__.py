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

"""nark provides generic time tracking functionality."""

import time

from easy_as_pypi_getver import get_version as _get_version

__all__ = (
    "get_version",
    "__package_name__",
    "__time_0__",
    "__PROFILING__",
    # Private:
    #  '_version_from_tags',
)

__PROFILING__ = True
# DEVS: Comment this out to see load times summary.
__PROFILING__ = False
__time_0__ = time.time()

# (lb): Seems a little redundant (see setup.cfg:[metadata]name)
# but not sure if way to get programmatically. This is closest
# solution that avoids hardcoding the library name in strings
# (which is something linter or runtime won't catch if wrong).
__package_name__ = "nark"

# This version is substituted on poetry-build by poetry-dynamic-versioning.
# - Consequently, __version__ remains empty when installed in 'editable' mode.
__version__ = ""


def get_version(include_head=False):
    return _get_version(
        package_name=__package_name__,
        reference_file=__file__,
        include_head=include_head,
    )
