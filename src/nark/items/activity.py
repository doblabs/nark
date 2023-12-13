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

from .category import Category
from .item_base import BaseItem

ActivityTuple = namedtuple(
    'ActivityTuple', ('pk', 'name', 'category', 'deleted', 'hidden'),
)


class Activity(BaseItem):
    """Storage agnostic class for activities."""

    def __init__(self, name, pk=None, category=None, deleted=False, hidden=False):
        """
        Initialize this instance.

        Args:
            name (str): This is the name of the activity. May contain whitespace!

            pk: The unique primary key used by the backend.

            category (Category): ``Category`` instance associated with this ``Activity``.

            deleted (bool): True if this ``Activity`` has been marked as deleted.

        Note:
            *Legacy hamster* basically treated ``(Activity.name, Category.name)`` as
            *composite keys*. As a consequence ``Activity.names`` themselves are not
            unique. They are only in combination with their associated categories name.
        """
        # [TODO]
        # Elaborate on the consequences of the deleted flag.

        super(Activity, self).__init__(pk, name)
        self.category = category
        self.deleted = bool(deleted)
        self.hidden = bool(hidden)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        # NOTE: (lb): Unlike Category.name=, not requiring ``not name``.
        if name is None:
            raise ValueError(_('Activity name must not be None.'))
        self._name = str(name)

    @classmethod
    def create_from_composite(cls, name, category_name, deleted=False):
        """
        Convenience method that allows creating a new instance providing
            the 'natural key'.

        Args:
            name (str): This activities name.
            category_name (str): Name of the associated category.
            deleted (bool): True if this ``Activity`` has been marked as deleted.

        Returns:
            Activity: A new ``Activity`` instance.

        Note:
            * Should future iterations extend ``Category`` this may turn problematic.
            * This method does not allow to specify a primary key as it is intended
              only for new instances, not ones retrieved by the backend.

        """
        category = Category(category_name)
        return cls(name, category=category, deleted=deleted)

    def as_tuple(self, include_pk=True):
        """
        Provide a tuple representation of this activities relevant 'fields'.

        Args:
            include_pk (bool): Whether to include the instances pk or not.
                Note that if ``False`` ``tuple.pk = False``!

        Returns:
            ActivityTuple: Representing this activities values.
        """
        pk = self.pk
        if not include_pk:
            pk = False
        if self.category:
            category = self.category.as_tuple(include_pk=include_pk)
        else:
            category = None
        return ActivityTuple(
            pk=pk,
            name=self.name,
            category=category,
            deleted=bool(self.deleted),
            hidden=bool(self.hidden),
        )

    def equal_fields(self, other):
        """
        Compare this instances fields with another activity.
            This excludes comparing the PK.

        Args:
            other (Activity): Activity to compare this instance with.

        Returns:
            bool: ``True`` if all fields but ``pk`` are equal, ``False`` if not.

        Note:
            This is particularly useful if you want to compare a new ``Activity``
            instance with a freshly created backend instance. As the latter will
            probably have a primary key assigned now and so ``__eq__`` would fail.
        """
        return self.as_tuple(include_pk=False) == other.as_tuple(include_pk=False)

    def __eq__(self, other):
        if other is not None and not isinstance(other, ActivityTuple):
            other = other.as_tuple()
        return self.as_tuple() == other

    def __hash__(self):
        """Naive hashing method."""
        return hash(self.as_tuple())

    def __str__(self):
        if self.category is None:
            full_name = '{name}'.format(name=self.name)
        else:
            full_name = '{name} ({category})'.format(
                name=self.name, category=self.category.name,
            )
        return full_name

