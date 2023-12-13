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

from . import BaseManager
from ..items.category import Category


class BaseCategoryManager(BaseManager):
    """
    Base class defining the minimal API for a CategoryManager implementation.
    """

    def __init__(self, *args, **kwargs):
        super(BaseCategoryManager, self).__init__(*args, **kwargs)

    # ***

    def save(self, category):
        """
        Save a Category to the backend.

        Args:
            category (nark.Category): Category instance to be saved.

        Returns:
            nark.Category: Saved Category

        Raises:
            TypeError: If the ``category`` parameter is not a valid
                ``Category`` instance.
        """
        return super(BaseCategoryManager, self).save(category, Category, named=True)

    # ***

    def get_or_create(self, category):
        """
        Check if we already got a category with that name, if not create one.

        This is a convenience method as it seems sensible to rather implement
        this once in our controller than having every client implementation
        deal with it anew.

        It is worth noting that the lookup completely ignores any PK contained in the
        passed category. This makes this suitable to just create the desired Category
        and pass it along. One way or the other one will end up with a persisted
        db-backed version.

        Args:
            category (nark.Category or None): The categories.

        Returns:
            nark.Category or None: The retrieved or created category. Either way,
                the returned Category will contain all data from the backend, including
                its primary key.
        """

        self.store.logger.debug(_("'{}' has been received.'.").format(category))
        if category:
            try:
                category = self.get_by_name(category)
            except KeyError:
                category = Category(category)
                category = self._add(category)
        else:
            # We want to allow passing ``category=None``, so we normalize here.
            category = None
        return category

    # ***

    def _add(self, category):
        """
        Add a ``Category`` to our backend.

        Args:
            category (nark.Category): ``Category`` to be added.

        Returns:
            nark.Category: Newly created ``Category`` instance.

        Raises:
            ValueError: When the category name was already present!
                It is supposed to be unique.
            ValueError: If category passed already got an PK.
                Indicating that update would be more appropriate.

        Note:
            * Legacy version stored the proper name as well as a ``lower(name)`` version
            in a dedicated field named ``search_name``.
        """
        raise NotImplementedError

    # ***

    def _update(self, category):
        """
        Update a ``Categories`` values in our backend.

        Args:
            category (nark.Category): Category to be updated.

        Returns:
            nark.Category: The updated Category.

        Raises:
            KeyError: If the ``Category`` can not be found by the backend.
            ValueError: If the ``Category().name`` is already being used by
                another ``Category`` instance.
            ValueError: If category passed does not have a PK.
        """
        raise NotImplementedError

    # ***

    def remove(self, category):
        """
        Remove a category.

        Any ``Activity`` referencing the passed category will be set to
        ``Activity().category=None``.

        Args:
            category (nark.Category): Category to be updated.

        Returns:
            None: If everything went ok.

        Raises:
            KeyError: If the ``Category`` can not be found by the backend.
            TypeError: If category passed is not an nark.Category instance.
            ValueError: If category passed does not have an pk.
        """
        raise NotImplementedError

    # ***

    def get(self, pk):
        """
        Get an ``Category`` by its primary key.

        Args:
            pk (int): Primary key of the ``Category`` to be fetched.

        Returns:
            nark.Category: ``Category`` with given primary key.

        Raises:
            KeyError: If no ``Category`` with this primary key can be found
                by the backend.
        """

        raise NotImplementedError

    # ***

    def get_by_name(self, name):
        """
        Look up a category by its name.

        Args:
            name (str): Unique name of the ``Category`` to we want to fetch.

        Returns:
            nark.Category: ``Category`` with given name.

        Raises:
            KeyError: If no ``Category`` with this name was found by the backend.
        """
        raise NotImplementedError

    # ***

    def get_all_by_usage(self, query_terms=None, **kwargs):
        """
        Similar to get_all(), but include count of Facts that reference each Category.
        """
        raise NotImplementedError

    # ***

    def gather(self, query_terms):
        """
        Return a list of ``Categories`` matching given criteria.
        """
        raise NotImplementedError

