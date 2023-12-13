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

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import NoResultFound

from ....managers.category import BaseCategoryManager
from ..objects import AlchemyCategory, AlchemyFact
from . import query_apply_true_or_not
from .manager_base import BaseAlchemyManager

__all__ = (
    'CategoryManager',
)


class CategoryManager(BaseAlchemyManager, BaseCategoryManager):
    """
    """
    def __init__(self, *args, **kwargs):
        super(CategoryManager, self).__init__(*args, **kwargs)

    # ***

    def get_or_create(self, category, raw=False, skip_commit=False):
        """
        Custom version of the default method in order to provide access
        to alchemy instances.

        Args:
            category (nark.Category): Category we want.
            raw (bool): Wether to return the AlchemyCategory instead.

        Returns:
            nark.Category or None: Category.
        """

        self.store.logger.debug("Received: {!r} / raw: {}".format(category, raw))

        try:
            category = self.get_by_name(category.name, raw=raw)
        except KeyError:
            category = self._add(category, raw=raw, skip_commit=skip_commit)
        return category

    # ***

    def _add(self, category, raw=False, skip_commit=False):
        """
        Add a new category to the database.

        This method should not be used by any client code. Call ``save`` to
        make the decission wether to modify an existing entry or to add a new
        one is done correctly.

        Args:
            category (nark.Category): nark Category instance.
            raw (bool): Wether to return the AlchemyCategory instead.

        Returns:
            nark.Category: Saved instance, as_hamster()

        Raises:
            ValueError: If the name to be added is already present in the db.
            ValueError: If category passed already got an PK. Indicating that
                update would be more appropriate.
        """
        self.adding_item_must_not_have_pk(category)

        alchemy_category = AlchemyCategory(
            pk=None,
            name=category.name,
            deleted=bool(category.deleted),
            hidden=bool(category.hidden),
        )

        result = self.add_and_commit(
            alchemy_category, raw=raw, skip_commit=skip_commit,
        )

        return result

    # ***

    def _update(self, category):
        """
        Update a given Category.

        Args:
            category (nark.Category): Category to be updated.

        Returns:
            nark.Category: Updated category.

        Raises:
            ValueError: If the new name is already taken.
            ValueError: If category passed does not have a PK.
            KeyError: If no category with passed PK was found.
        """

        self.store.logger.debug("Received: {!r}".format(category))

        if not category.pk:
            message = _(
                "The Category passed ('{!r}') does not have a PK."
                " We do not know which entry to modify."
            ).format(category)
            self.store.logger.error(message)
            raise ValueError(message)
        alchemy_category = self.store.session.query(AlchemyCategory).get(category.pk)
        if not alchemy_category:
            message = _("No Category with PK ‘{}’ was found.").format(category.pk)
            self.store.logger.error(message)
            raise KeyError(message)
        alchemy_category.name = category.name

        try:
            self.store.session.commit()
        except IntegrityError as err:
            message = _(
                "An error occured! Is category.name already present in the database?"
                " / Error: '{}'."
            ).format(str(err))
            self.store.logger.error(message)
            raise ValueError(message)

        return alchemy_category.as_hamster(self.store)

    # ***

    def remove(self, category):
        """
        Delete a given category.

        Args:
            category (nark.Category): Category to be removed.

        Returns:
            None: If everything went alright.

        Raises:
            KeyError: If the ``Category`` can not be found by the backend.
            ValueError: If category passed does not have an pk.
        """

        self.store.logger.debug("Received: {!r}".format(category))

        if not category.pk:
            message = _(
                "Category ‘{!r}’ has no PK. Are you trying to remove a new Category?"
            ).format(category)
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_category = self.store.session.query(AlchemyCategory).get(category.pk)
        if not alchemy_category:
            message = _("No Category with PK ‘{}’ was found.").format(category.pk)
            self.store.logger.error(message)
            raise KeyError(message)

        self.store.session.delete(alchemy_category)
        self.store.session.commit()
        self.store.logger.debug("Deleted: {!r}".format(category))

    # ***

    def get(self, pk, deleted=None):
        """
        Return a category based on their pk.

        Args:
            pk (int): PK of the category to be retrieved.

        Returns:
            nark.Category: Category matching given PK.

        Raises:
            KeyError: If no such PK was found.

        Note:
            We need this for now, as the service just provides pks, not names.
        """

        self.store.logger.debug("Received PK: ‘{}’".format(pk))

        if deleted is None:
            result = self.store.session.query(AlchemyCategory).get(pk)
        else:
            query = self.store.session.query(AlchemyCategory)
            query = query.filter(AlchemyCategory.pk == pk)
            query = query_apply_true_or_not(query, AlchemyCategory.deleted, deleted)
            results = query.all()
            assert len(results) <= 1
            result = results[0] if results else None

        if not result:
            message = _("No Category with PK ‘{}’ was found.").format(pk)
            self.store.logger.error(message)
            raise KeyError(message)
        self.store.logger.debug("Returning: {!r}".format(result))
        return result.as_hamster(self.store)

    # ***

    def get_by_name(self, name, raw=False):
        """
        Return a category based on its name.

        Args:
            name (str): Unique name of the category.
            raw (bool): Whether to return the AlchemyCategory instead.

        Returns:
            nark.Category: Category of given name.

        Raises:
            KeyError: If no category matching the name was found.

        """
        self.store.logger.debug("Received name: ‘{}’ / raw: {}".format(name, raw))

        try:
            result = self.store.session.query(AlchemyCategory).filter_by(name=name).one()
        except NoResultFound:
            message = _("No Category named ‘{}’ was found.").format(name)
            self.store.logger.debug(message)
            raise KeyError(message)

        if not raw:
            result = result.as_hamster(self.store)
            self.store.logger.debug("Returning: {!r}.".format(result))
        return result

    # ***
    # *** gather() call-outs (used by get_all/get_all_by_usage).
    # ***

    @property
    def _gather_query_alchemy_cls(self):
        return AlchemyCategory

    @property
    def _gather_query_order_by_name_col(self):
        return 'category'

    def _gather_query_requires_fact(self, qt, compute_usage):
        requires_fact_table = super(
            CategoryManager, self
        )._gather_query_requires_fact(qt, compute_usage)

        # Ensure _gather_query_start_aggregate called -- and that we
        # select from Fact, joined Activity, joined Category -- if
        # the user is matching on or ordering by Activity.
        requires_fact_table = (
            requires_fact_table
            or qt.match_activities
            or qt.sort_cols_has_any('activity')
        )

        return requires_fact_table

    def _gather_query_start_aggregate(self, qt, agg_cols):
        query = self.store.session.query(AlchemyFact, *agg_cols)
        query = query.outerjoin(AlchemyFact.activity)
        query = query.outerjoin(AlchemyCategory)
        return query

    # ***

