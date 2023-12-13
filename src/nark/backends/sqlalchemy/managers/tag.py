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

from ....managers.tag import BaseTagManager
from ..objects import (
    AlchemyActivity,
    AlchemyCategory,
    AlchemyFact,
    AlchemyTag,
    fact_tags
)
from . import query_apply_true_or_not
from .manager_base import BaseAlchemyManager

__all__ = (
    'TagManager',
)


class TagManager(BaseAlchemyManager, BaseTagManager):
    """
    """
    def __init__(self, *args, **kwargs):
        super(TagManager, self).__init__(*args, **kwargs)

    # ***

    def get_or_create(self, tag, raw=False, skip_commit=False):
        """
        Custom version of the default method in order to provide access to
        alchemy instances.

        Args:
            tag (nark.Tag): Tag we want.
            raw (bool): Wether to return the AlchemyTag instead.

        Returns:
            nark.Tag or None: Tag.
        """
        self.store.logger.debug("Received: {!r} / raw: {}".format(tag, raw))

        try:
            tag = self.get_by_name(tag.name, raw=raw)
        except KeyError:
            tag = self._add(tag, raw=raw, skip_commit=skip_commit)
        return tag

    # ***

    def _add(self, tag, raw=False, skip_commit=False):
        """
        Add a new tag to the database.

        This method should not be used by any client code. Call ``save`` to make
        the decission wether to modify an existing entry or to add a new one is
        done correctly..

        Args:
            tag (nark.Tag): nark Tag instance.
            raw (bool): Wether to return the AlchemyTag instead.

        Returns:
            nark.Tag: Saved instance, as_hamster()

        Raises:
            ValueError: If the name to be added is already present in the db.
            ValueError: If tag passed already got an PK. Indicating that update
                would be more appropriate.
        """
        self.adding_item_must_not_have_pk(tag)

        alchemy_tag = AlchemyTag(
            pk=None,
            name=tag.name,
            deleted=bool(tag.deleted),
            hidden=bool(tag.hidden),
        )

        result = self.add_and_commit(
            alchemy_tag, raw=raw, skip_commit=skip_commit,
        )

        return result

    # ***

    def _update(self, tag):
        """
        Update a given Tag.

        Args:
            tag (nark.Tag): Tag to be updated.

        Returns:
            nark.Tag: Updated tag.

        Raises:
            ValueError: If the new name is already taken.
            ValueError: If tag passed does not have a PK.
            KeyError: If no tag with passed PK was found.
        """
        self.store.logger.debug("Received: {!r}".format(tag))

        if not tag.pk:
            message = _(
                "The Tag passed ('{!r}') does not have a PK."
                " We do not know which entry to modify."
            ).format(tag)
            self.store.logger.error(message)
            raise ValueError(message)
        alchemy_tag = self.store.session.query(AlchemyTag).get(tag.pk)
        if not alchemy_tag:
            message = _("No Tag with PK ‘{}’ was found.").format(tag.pk)
            self.store.logger.error(message)
            raise KeyError(message)
        alchemy_tag.name = tag.name

        try:
            self.store.session.commit()
        except IntegrityError as err:
            message = _(
                "An error occured! Are you sure that tag.name is not "
                "already present in the database? Error: '{}'."
            ).format(str(err))
            self.store.logger.error(message)
            raise ValueError(message)

        return alchemy_tag.as_hamster(self.store)

    # ***

    def remove(self, tag):
        """
        Delete a given tag.

        Args:
            tag (nark.Tag): Tag to be removed.

        Returns:
            None: If everything went alright.

        Raises:
            KeyError: If the ``Tag`` can not be found by the backend.
            ValueError: If tag passed does not have an pk.
        """

        self.store.logger.debug("Received: {!r}".format(tag))

        if not tag.pk:
            message = _(
                "Tag ‘{!r}’ has no PK. Are you trying to remove a new Tag?"
            ).format(tag)
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_tag = self.store.session.query(AlchemyTag).get(tag.pk)
        if not alchemy_tag:
            message = _("No Tag with PK ‘{}’ was found.").format(tag.pk)
            self.store.logger.error(message)
            raise KeyError(message)

        self.store.session.delete(alchemy_tag)
        self.store.session.commit()
        self.store.logger.debug("Deleted: {!r}".format(tag))

    # ***

    def get(self, pk, deleted=None):
        """
        Return a tag based on their pk.

        Args:
            pk (int): PK of the tag to be retrieved.

        Returns:
            nark.Tag: Tag matching given PK.

        Raises:
            KeyError: If no such PK was found.

        Note:
            We need this for now, as the service just provides pks, not names.
        """
        self.store.logger.debug("Received PK: ‘{}’".format(pk))

        if deleted is None:
            result = self.store.session.query(AlchemyTag).get(pk)
        else:
            query = self.store.session.query(AlchemyTag)
            query = query.filter(AlchemyTag.pk == pk)
            query = query_apply_true_or_not(query, AlchemyTag.deleted, deleted)
            results = query.all()
            assert len(results) <= 1
            result = results[0] if results else None

        if not result:
            message = _("No Tag with PK ‘{}’ was found.").format(pk)
            self.store.logger.error(message)
            raise KeyError(message)
        self.store.logger.debug("Returning: {!r}".format(result))
        return result.as_hamster(self.store)

    # ***

    def get_by_name(self, name, raw=False):
        """
        Return a tag based on its name.

        Args:
            name (str): Unique name of the tag.
            raw (bool): Wether to return the AlchemyTag instead.

        Returns:
            nark.Tag: Tag of given name.

        Raises:
            KeyError: If no tag matching the name was found.

        """
        self.store.logger.debug("Received name: ‘{}’ / raw: {}.".format(name, raw))

        try:
            result = self.store.session.query(AlchemyTag).filter_by(name=name).one()
        except NoResultFound:
            message = _("No Tag named ‘{}’ was found.").format(name)
            self.store.logger.debug(message)
            raise KeyError(message)

        if not raw:
            result = result.as_hamster(self.store)
            self.store.logger.debug("Returning: {!r}".format(result))
        return result

    # ***
    # *** gather() call-outs (used by get_all/get_all_by_usage).
    # ***

    @property
    def _gather_query_alchemy_cls(self):
        return AlchemyTag

    @property
    def _gather_query_order_by_name_col(self):
        return 'tag'

    def _gather_query_requires_fact(self, qt, compute_usage):
        requires_fact_table = super(
            TagManager, self
        )._gather_query_requires_fact(qt, compute_usage)

        # (lb): I'm not sure the utility of querying Tag and sorting by
        # Activity, but we can easily support it.
        requires_fact_table = (
            requires_fact_table
            or qt.sort_cols_has_any('activity')
            or qt.sort_cols_has_any('category')
        )

        return requires_fact_table

    def _gather_query_start_aggregate(self, qt, agg_cols):
        # NOTE: We do not need a subquery here, unlike in gather_fact.py.
        #       - In _get_all_prepare_tags_subquery, which adds tags to the Fact
        #         gather query, the join-on-tags is performed in a subquery
        #         so that the (outer) group by aggregate functions do not
        #         inadvertently count each Fact more than once. In the case of
        #         a Fact gather, the tags names are being joined together for
        #         each Fact. But here, we actually want all the rows to be
        #         included in the aggregates, because we're counting usage the
        #         other way around -- how many Facts use each Tag; rather than
        #         how it is for the Fact gather, which is how many Tags of each
        #         name there are for each Fact. In any case, mostly just a note
        #         to self, because I looked at this and thought it smelled funny,
        #         because there's a subquery in the Fact gather query; but we
        #         don't need one here.
        query = self.store.session.query(AlchemyTag, *agg_cols)
        query = query.join(
            fact_tags, AlchemyTag.pk == fact_tags.columns.tag_id,
        )
        query = query.join(AlchemyFact)
        return query

    def query_criteria_filter_by_activities(self, query, qt):
        query, criteria = super(
            TagManager, self,
        ).query_criteria_filter_by_activities(query, qt)
        # (lb): I'm not sure the utility of querying Tag and sorting by
        # Activity, but we can easily support it.
        join_activity = bool(criteria) or qt.sort_cols_has_any('activity')
        if join_activity:
            query = query.join(AlchemyActivity)
        # (lb): I'm not sure if there's a way to check the query to see
        #       if it contains a table already; or whether the query is
        #       smart enough to discard multiple joins of the same table.
        #       So make a note to self that we joined the Activity table.
        qt.joined_activity = join_activity
        return query, criteria

    def query_criteria_filter_by_categories(self, query, qt):
        query, criteria = super(
            TagManager, self,
        ).query_criteria_filter_by_categories(query, qt)
        # (lb): I'm not sure the utility of querying Tag and sorting by
        # Category, but we can easily support it.
        join_category = bool(criteria) or qt.sort_cols_has_any('category')
        if join_category:
            if not qt.joined_activity:
                query = query.join(AlchemyActivity)
            query = query.join(AlchemyCategory)
        return query, criteria

    # ***

