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

"""Base class for Nark item instances."""

__all__ = ('BaseItem', )


class BaseItem(object):
    """Base class for all items."""

    def __init__(self, pk, name):
        self.pk = pk
        self.name = name

    def __repr__(self, ignore=()):
        parts = []
        for key in sorted(self.__dict__.keys()):
            if key in ignore:
                continue
            parts.append(
                "{key}={val}".format(key=key, val=repr(getattr(self, key)))
            )
        repred = "{cls}({parts})".format(
            cls=self.__class__.__name__, parts=', '.join(parts),
        )
        return repred

    @property
    def unstored(self):
        return (not self.pk) or (self.pk < 0)

