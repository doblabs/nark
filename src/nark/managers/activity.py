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
from ..items.activity import Activity


class BaseActivityManager(BaseManager):
    """
    Base class defining the minimal API for a ActivityManager implementation.
    """
    def __init__(self, *args, **kwargs):
        super(BaseActivityManager, self).__init__(*args, **kwargs)

    # ***

    def save(self, activity):
        """
        Save an ``Activity`` to the backend.

        Args:
            activity (nark.Activity): ``Activity`` to be saved.

        Returns:
            nark.Activity: The saved ``Activity``.

        Raises:
            TypeError: If the ``activity`` parameter is not a valid
                ``Activity`` instance.
        """
        return super(BaseActivityManager, self).save(activity, Activity, named=True)

    # ***

    def get_or_create(self, activity):
        """
        Convenience method to either get an activity matching the specs
            or create a new one.

        Args:
            activity (nark.Activity): The activity we want.

        Returns:
            nark.Activity: The retrieved or created activity
        """
        self.store.logger.debug(_("'{}' has been received.".format(activity)))
        try:
            activity = self.get_by_composite(activity.name, activity.category)
        except KeyError:
            activity = self.save(
                Activity(
                    activity.name,
                    category=activity.category,
                    deleted=bool(activity.deleted),
                )
            )
        return activity

    # ***

    def _add(self, activity):
        """
        Add a new ``Activity`` instance to the database.

        Args:
            activity (nark.Activity): The ``Activity`` to be added.

        Returns:
            nark.Activity: The newly created ``Activity``.

        Raises:
            ValueError: If the passed activity has a PK.
            ValueError: If the category/activity.name combination to be added is
                already present in the db.

        Note:
            According to ``storage.db.Storage.__add_activity``: when adding
            a new activity with a new category, this category does not get
            created but instead this activity.category=None. This makes sense
            as categories passed are just ids, we however can pass full
            category objects. At the same time, this approach allows to add
            arbitrary category.id as activity.category without checking their
            existence. This may lead to db anomalies.
        """
        raise NotImplementedError

    # ***

    def _update(self, activity):
        """
        Update values for a given activity.

        Which activity to refer to is determined by the passed PK new values
        are taken from passed activity as well.

        Args:
            activity (nark.Activity): Activity to be updated.

        Returns:
            nark.Activity: Updated activity.
        Raises:
            ValueError: If the new name/category.name combination is already taken.
            ValueError: If the the passed activity does not have a PK assigned.
            KeyError: If the the passed activity.pk can not be found.

        Note:
            Seems to modify ``index``.
        """

        raise NotImplementedError

    # ***

    def remove(self, activity):
        """
        Remove an ``Activity`` from the database.import

        If the activity to be removed is associated with any ``Fact``-instances,
        we set ``activity.deleted=True`` instead of deleting it properly.
        If it is not, we delete it from the backend.

        Args:
            activity (nark.Activity): The activity to be removed.

        Returns:
            bool: True

        Raises:
            KeyError: If the given ``Activity`` can not be found in the database.

        Note:
            Should removing the last activity of a category also trigger category
            removal?
        """

        raise NotImplementedError

    # ***

    def get(self, pk):
        """
        Return an activity based on its primary key.

        Args:
            pk (int): Primary key of the activity

        Returns:
            nark.Activity: Activity matching primary key.

        Raises:
            KeyError: If the primary key can not be found in the database.
        """
        raise NotImplementedError

    # ***

    # NOTE: Unlike Category and Tag, there is no Activity.get_by_name,
    #       but you'll find Activity.get_by_composite instead. This is
    #       because get_by_name returns one result, but more than one
    #       Activity may have the same name, so we use the Category to
    #       narrow down the matches to just one (or none).

    def get_by_composite(self, name, category):
        """
        Lookup for unique 'name/category.name'-composite key.

        This method utilizes that to return the corresponding entry or None.

        Args:
            name (str): Name of the ``Activities`` in question.

            category (nark.Category or None): ``Category`` of the activities.
                May be None.

        Returns:
            nark.Activity: The corresponding activity

        Raises:
            KeyError: If the composite key can not be found.
        """
        # [FIXME]
        # Handle resurrection. See legacy
        # ``nark.storage.db.__get_activity_by_name``

        raise NotImplementedError

    # ***

    def get_all_by_usage(self, query_terms=None, **kwargs):
        """
        Similar to get_all(), but include count of Facts that reference each Activity.
        """
        raise NotImplementedError

    # ***

    def gather(self, query_terms):
        """
        Return a list of ``Activities`` matching given criteria.
        """
        raise NotImplementedError

