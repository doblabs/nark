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

"""Submodule providing a SQLAlchemy storage backend for ``nark``."""

# Normally, to control lazy-loading, we wouldn't export classes from here,
# but the store is loaded dynamically, so we need to export classes here
# so that the factory generator doesn't have to explicitly import them all.
# (lb): Or something.
#   Search: importlib.import_module
from .storage import SQLAlchemyStore  # noqa: F401

