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
from ..items.tag import Tag


class BaseTagManager(BaseManager):
    """
    Base class defining the minimal API for a TagManager implementation.
    """

    def __init__(self, *args, **kwargs):
        super(BaseTagManager, self).__init__(*args, **kwargs)

    # ***

    def save(self, tag):
        """
        Save a Tag to the backend.

        Args:
            tag (nark.Tag): Tag instance to be saved.

        Returns:
            nark.Tag: Saved Tag

        Raises:
            TypeError: If the ``tag`` parameter is not a valid ``Tag`` instance.
        """
        return super(BaseTagManager, self).save(tag, Tag, named=True)

    # ***

    def get_or_create(self, tag):
        """
        Check if we already got a tag with that name, if not create one.

        This is a convenience method as it seems sensible to rather implement
        this once in our controller than having every client implementation
        deal with it anew.

        It is worth noting that the lookup completely ignores any PK contained in the
        passed tag. This makes this suitable to just create the desired Tag
        and pass it along. One way or the other one will end up with a persisted
        db-backed version.

        Args:
            tag (nark.Tag or None): The categories.

        Returns:
            nark.Tag or None: The retrieved or created tag. Either way,
                the returned Tag will contain all data from the backend, including
                its primary key.
        """
        self.store.logger.debug(_("'{}' has been received.'.").format(tag))
        if tag:
            try:
                tag = self.get_by_name(tag)
            except KeyError:
                tag = Tag(tag)
                tag = self._add(tag)
        else:
            # We want to allow passing ``tag=None``, so we normalize here.
            tag = None
        return tag

    # ***

    def _add(self, tag):
        """
        Add a ``Tag`` to our backend.

        Args:
            tag (nark.Tag): ``Tag`` to be added.

        Returns:
            nark.Tag: Newly created ``Tag`` instance.

        Raises:
            ValueError: When the tag name was already present! It is supposed to be
            unique.
            ValueError: If tag passed already got an PK. Indicating that update would
                be more appropriate.
        """
        raise NotImplementedError

    # ***

    def _update(self, tag):
        """
        Update a ``Tags`` values in our backend.

        Args:
            tag (nark.Tag): Tag to be updated.

        Returns:
            nark.Tag: The updated Tag.

        Raises:
            KeyError: If the ``Tag`` can not be found by the backend.
            ValueError: If the ``Tag().name`` is already being used by
                another ``Tag`` instance.
            ValueError: If tag passed does not have a PK.
        """
        raise NotImplementedError

    # ***

    def remove(self, tag):
        """
        Remove a tag.

        Any ``Fact`` referencing the passed tag will have this tag removed.

        Args:
            tag (nark.Tag): Tag to be updated.

        Returns:
            None: If everything went ok.

        Raises:
            KeyError: If the ``Tag`` can not be found by the backend.
            TypeError: If tag passed is not an nark.Tag instance.
            ValueError: If tag passed does not have an pk.
        """
        raise NotImplementedError

    # ***

    def get(self, pk):
        """
        Get an ``Tag`` by its primary key.

        Args:
            pk (int): Primary key of the ``Tag`` to be fetched.

        Returns:
            nark.Tag: ``Tag`` with given primary key.

        Raises:
            KeyError: If no ``Tag`` with this primary key can be found by the backend.
        """

        raise NotImplementedError

    # ***

    def get_by_name(self, name):
        """
        Look up a tag by its name.

        Args:
            name (str): Unique name of the ``Tag`` to we want to fetch.

        Returns:
            nark.Tag: ``Tag`` with given name.

        Raises:
            KeyError: If no ``Tag`` with this name was found by the backend.
        """
        raise NotImplementedError

    # ***

    def get_all_by_usage(self, query_terms=None, **kwargs):
        """
        Similar to get_all(), but include count of Facts that reference each Tag.
        """
        raise NotImplementedError

    # ***

    def gather(self, query_terms):
        """
        Return a list of ``Tags`` matching given criteria.
        """
        raise NotImplementedError

