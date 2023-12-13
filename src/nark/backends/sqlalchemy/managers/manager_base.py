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

"""``nark`` storage object managers."""

from gettext import gettext as _

from sqlalchemy.exc import IntegrityError

from .gather_base import GatherBaseAlchemyManager

__all__ = (
    'BaseAlchemyManager',
)


class BaseAlchemyManager(GatherBaseAlchemyManager):
    """Base class for sqlalchemy managers."""

    def __init__(self, *args, **kwargs):
        super(BaseAlchemyManager, self).__init__(*args, **kwargs)

    # ***

    def add_and_commit(self, alchemy_item, raw=False, skip_commit=False):
        """
        Adds the item to the data store, and perhaps calls commit.

        Generally, unless importing Facts, the session is committed
        after an item is added or updated. However, when adding or
        updating a Fact, we might also create other items (activity,
        category, tags), so we delay committing until everything is
        added/updated.
        """
        def _add_and_commit():
            session_add()
            session_commit_maybe()
            result = prepare_item()
            self.store.logger.debug(_("Added item: {!r}".format(result)))
            return result

        def session_add():
            self.store.session.add(alchemy_item)

        def session_commit_maybe():
            if skip_commit:
                return
            try:
                self.store.session.commit()
            except IntegrityError as err:
                message = _(
                    "An error occured! Are you sure that the {0}'s name "
                    "or ID is not already present? Error: '{1}'.".format(
                        self.__class__.__name__, err,
                    )
                )
                self.store.logger.error(message)
                raise ValueError(message)

        def prepare_item():
            result = alchemy_item
            if not raw:
                result = alchemy_item.as_hamster(self.store)
            return result

        return _add_and_commit()

    # ***

    def get_all(self, query_terms=None, **kwargs):
        """Returns matching items from the data store; and stats, if requested.

        get_all() is similar to get_all_by_usage(), but get_all() prefers not to
        include usage statistics in the results, and prefers to sort by item name.

        See gather method and QueryTerms class docstrings for more details.
        """
        query_terms, kwargs = self._gather_prepare_query_terms(query_terms, **kwargs)
        if query_terms.include_stats is None:
            query_terms.include_stats = False
        if query_terms.sort_cols is None:
            query_terms.sort_cols = ('name',)
        return super(BaseAlchemyManager, self).get_all(query_terms, **kwargs)

    def get_all_by_usage(self, query_terms=None, **kwargs):
        """Returns matching items from the data store; and stats, if requested.

        get_all_by_usage() is an alias to get_all() that prefers to enable
        include_stats, and to sort by the usage calculation.

        See gather method and QueryTerms class docstrings for more details.
        """
        query_terms, kwargs = self._gather_prepare_query_terms(query_terms, **kwargs)
        if query_terms.include_stats is None:
            query_terms.include_stats = True
        if query_terms.sort_cols is None:
            query_terms.sort_cols = ('usage',)
        return super(BaseAlchemyManager, self).get_all(query_terms, **kwargs)

    # ***

# ***

