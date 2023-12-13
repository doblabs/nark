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

from gettext import gettext as _

from collections import namedtuple

from .item_base import BaseItem

CategoryTuple = namedtuple(
    'CategoryTuple', ('pk', 'name', 'deleted', 'hidden'),
)


class Category(BaseItem):
    """Storage agnostic class for categories."""

    def __init__(self, name, pk=None, deleted=False, hidden=False):
        """
        Initialize this instance.

        Args:
            name (str): The name of the category. May contain whitespace!
            pk: The unique primary key used by the backend.
        """

        super(Category, self).__init__(pk, name)
        self.deleted = bool(deleted)
        self.hidden = bool(hidden)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if name is None:
            raise ValueError(_('Category name must not be None.'))
        self._name = str(name)

    def as_tuple(self, include_pk=True):
        """
        Provide a tuple representation of this categories relevant 'fields'.

        Args:
            include_pk (bool): Whether to include the instances pk or not. Note that if
            ``False`` ``tuple.pk = False``!

        Returns:
            CategoryTuple: Representing this categories values.
        """
        pk = self.pk
        if not include_pk:
            pk = False
        cat_tup = CategoryTuple(
            pk=pk,
            name=self.name,
            deleted=bool(self.deleted),
            hidden=bool(self.hidden),
        )
        return cat_tup

    def equal_fields(self, other):
        """
        Compare this instances fields with another category.
        This excludes comparing the PK.

        Args:
            other (Category): Category to compare this instance with.

        Returns:
            bool: ``True`` if all fields but ``pk`` are equal, ``False`` if not.

        Note:
            This is particularly useful if you want to compare a new
            ``Category`` instance with a freshly created backend instance. As
            the latter will probably have a primary key assigned now and so
            ``__eq__`` would fail.
        """
        if other:
            other = other.as_tuple(include_pk=False)
        else:
            other = None

        return self.as_tuple(include_pk=False) == other

    def __eq__(self, other):
        if other is not None and not isinstance(other, CategoryTuple):
            other = other.as_tuple()
        return self.as_tuple() == other

    def __hash__(self):
        """Naive hashing method."""
        return hash(self.as_tuple())

    def __str__(self):
        return '{name}'.format(name=self.name)

