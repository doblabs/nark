# This file exists within 'nark':
#
#   https://github.com/tallybark/nark
#
# Copyright © 2018-2020 Landon Bouma. All rights reserved.
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

"""Base aggregate item fetch implementation."""

from sqlalchemy import func
from sqlalchemy.sql.expression import and_, or_

from ..objects import AlchemyActivity, AlchemyCategory, AlchemyFact, AlchemyTag

from . import (
    query_apply_limit_offset,
    query_prepare_datetime,
    query_sort_order_at_index,
)

__all__ = (
    'GatherBaseAlchemyManager',
)


class GatherBaseAlchemyManager(object):
    """Base class aggregate query implementation for BaseAlchemyManager."""

    def __init__(self, *args, **kwargs):
        super(GatherBaseAlchemyManager, self).__init__(*args, **kwargs)

    # ***

    def gather(self, query_terms):
        """
        Returns matching items from the data store; and stats, if requested.

        Args:
            query_terms (nark.managers.query_terms.QueryTerms, required):
                The QueryTerms object defines the query settings used to find
                matching items, and it also defines how the results should be
                packaged. See the QueryTerms class for details.

        Returns:
            list: A list of matching item instances or (item, *statistics) tuples.
            - If raw results are requested, each item is the Alchemy<Item> object
              from SQLAlchemy (e.g., nark.backends.sqlalchemy.objects.AlchemyActivity).
              Otherwise, by default, each item is a first-class <Item> instance,
              hydrated from the Alchemy object (e.g., nark.items.activity.Activity).
            - If include_stats is requested, each result is a tuple consisting of
              the item as the first element, followed by additional calculated
              values (aggregates) pertaining to the query.
            - The list of results will be ordered according to the QueryTerms
              sort_cols and sort_orders options, if possible. Otherwise, for
              some queries that concatenate and post-process a value that is to
              be sorted on, the sorting is left as an exercise for the caller
              (because often the caller must do some post-processing of its own,
              so this method does not waste the cycles using, say, a subquery to
              do the sort in an outer query).
        """
        qt = query_terms

        # Get the Alchemy class, e.g., AlchemyActivity.
        alchemy_cls = self._gather_query_alchemy_cls

        # Compute the aggregate values if the user wants them returned with
        # the results, or if the user wants to sort the results accordingly.
        compute_usage = (
            qt.include_stats
            or qt.sort_cols_has_any('start', 'usage', 'time')
        )
        # If user is requesting filtering or sorting according to time, join Fact.
        requires_fact_table = self._gather_query_requires_fact(qt, compute_usage)

        def _gather_items():
            self.store.logger.debug(qt)

            query, agg_cols = _gather_query_start()

            query = self.query_filter_by_fact_times(
                query, qt.since, qt.until, qt.endless, qt.partial,
            )

            query = self.query_filter_by_activities(query, qt)

            query = self.query_filter_by_categories(query, qt)

            # (lb): We could add the match_tags option, but it'd be tricky
            # (we'd need to join on Facts, etc.), and does not seem of much
            # utility.
            #  query = self.query_filter_by_tags(query, qt)

            query = query_filter_by_search_term(query)

            query = self.query_filter_by_item_pk(query, alchemy_cls, qt.key)

            # FIXME/2020-06-03: Activity.deleted should not be used/useful.
            # (lb): And I've got some deleted = 0 and some deleted = 1 in my
            # database, but mostly deleted IS NULL, so skip deleted in WHERE
            # for attributes. (Remove this when removing deleted/hidden.)
            #  from . import query_apply_true_or_not
            #  query = query_apply_true_or_not(query, alchemy_cls.deleted, qt.deleted)

            query = query_group_by_aggregate(query, agg_cols)

            has_facts = requires_fact_table
            query = self.query_order_by_sort_cols(query, qt, has_facts, *agg_cols)

            query = query_apply_limit_offset(query, qt.limit, qt.offset)

            query = query_select_with_entities(query, agg_cols)

            self.query_prepared_trace(query)

            if qt.count_results:
                results = query.count()
            else:
                results = query.all()
                results = _gather_process_results(results)

            return results

        # ***

        def _gather_query_start():
            agg_cols = []

            if not requires_fact_table:
                query = self._gather_query_start_timeless(qt, alchemy_cls)
            else:
                if qt.include_stats or qt.sort_cols_has_any('usage'):
                    # (lb): I tried the COUNT() on the pk, e.g.,
                    #   count_col = func.count(alchemy_cls.pk).label('uses')
                    # but then if alchemy_cls is NULL (e.g., if Fact has an
                    # Activity where Category IS NULL), the count is 0, (e.g.,
                    # because COUNT(categories.id)). So do a broad COUNT(*), and
                    # then NULL rows will be counted (e.g., try `dob usage cat`).
                    # Just be sure there's a GROUP BY, otherwise the COUNT(*)
                    # will collapse all rows.
                    count_col = func.count().label('uses')
                    agg_cols.append(count_col)
                if qt.include_stats or qt.sort_cols_has_any('time'):
                    time_col = func.sum(
                        func.julianday(AlchemyFact.end)
                        - func.julianday(AlchemyFact.start)
                    ).label('span')
                    agg_cols.append(time_col)
                query = self._gather_query_start_aggregate(qt, agg_cols)

            return query, agg_cols

        # ***

        def query_filter_by_search_term(query):
            if not qt.search_terms:
                return query

            filters = []
            for term in qt.search_terms:
                filters.append(alchemy_cls.name.ilike('%{}%'.format(term)))
            query = query.filter(or_(*filters))

            return query

        # ***

        def query_group_by_aggregate(query, agg_cols):
            if not agg_cols and not requires_fact_table:
                return query
            query = query.group_by(alchemy_cls.pk)
            return query

        # ***

        def query_select_with_entities(query, agg_cols):
            if not agg_cols and not requires_fact_table:
                return query
            # (lb): The aggregate query SELECTs all Fact columns, and it OUTER
            #  JOINs and GROUPs BY activities and categories or tags to produce
            #  the counts. But the Fact is meaningless after the group-by, as it
            #  represents a grouping. And we're not after the Fact; we want the
            #  attribute item (Activity, Category, or Tag). So we use with_entities
            #  to tell SQLAlchemy which columns to select -- it'll transform the
            #  query so that the SELECT fetches all the Activity columns; but the
            #  JOIN and GROUP BY remain the same. (Hey hey it's magic.)
            query = query.with_entities(alchemy_cls, *agg_cols)
            return query

        # ***

        def _gather_process_results(records):
            return self.query_process_results(
                records,
                raw=qt.raw,
                include_stats=compute_usage,
                requested_usage=qt.include_stats,
            )

        # ***

        return _gather_items()

    # ***

    def _gather_query_start_timeless(self, qt, alchemy_cls):
        # Query on, e.g., AlchemyActivity.
        query = self.store.session.query(alchemy_cls)
        return query

    def _gather_query_start_aggregate(self, qt, agg_cols):
        raise NotImplementedError

    # ***

    def _gather_query_requires_fact(self, qt, compute_usage):
        requires_fact_table = (
            compute_usage
            or qt.since
            or qt.until
            or qt.endless
        )
        return requires_fact_table

    # ***

    def query_filter_by_item_pk(self, query, alchemy_cls, key):
        if key is None:
            return query
        return query.filter(alchemy_cls.pk == key)

    # ***

    def query_filter_by_fact_times(
        self, query, since=None, until=None, endless=False, partial=False,
    ):
        def _query_filter_by_fact_times(query, since, until, endless, partial):
            fmt_since = query_prepare_datetime(since) if since else None
            fmt_until = query_prepare_datetime(until) if until else None
            if partial:
                query = _get_partial_overlaps(query, fmt_since, fmt_until)
            else:
                query = _get_complete_overlaps(query, fmt_since, fmt_until, endless)
            return query

        def _get_partial_overlaps(query, since, until):
            """Return all facts where either start or end falls within the timeframe."""
            if since and not until:
                # (lb): Checking AlchemyFact.end >= since is sorta redundant,
                # because AlchemyFact.start >= since should guarantee that.
                query = query.filter(
                    or_(
                        func.datetime(AlchemyFact.start) >= since,
                        func.datetime(AlchemyFact.end) >= since,
                    ),
                )
            elif not since and until:
                # (lb): Checking AlchemyFact.start <= until is sorta redundant,
                # because AlchemyFact.end <= until should guarantee that.
                # - Except maybe for an Active Fact?
                query = query.filter(
                    or_(
                        func.datetime(AlchemyFact.start) <= until,
                        func.datetime(AlchemyFact.end) <= until,
                    ),
                )
            elif since and until:
                query = query.filter(or_(
                    and_(
                        func.datetime(AlchemyFact.start) >= since,
                        func.datetime(AlchemyFact.start) <= until,
                    ),
                    and_(
                        func.datetime(AlchemyFact.end) >= since,
                        func.datetime(AlchemyFact.end) <= until,
                    ),
                ))
            else:
                pass
            return query

        def _get_complete_overlaps(query, since, until, endless=False):
            """Return all facts with start and end within the timeframe."""
            if since:
                query = query.filter(func.datetime(AlchemyFact.start) >= since)
            if until:
                query = query.filter(func.datetime(AlchemyFact.end) <= until)
            elif endless:
                query = query.filter(AlchemyFact.end == None)  # noqa: E711
            return query

        return _query_filter_by_fact_times(query, since, until, endless, partial)

    # ***

    def query_filter_by_activities(self, query, qt):
        query, criteria = self.query_criteria_filter_by_activities(query, qt)
        query = query.filter(or_(*criteria))
        return query

    def query_criteria_filter_by_activities(self, query, qt):
        criteria = []
        for activity in qt.match_activities or []:
            criterion = self.query_filter_by_activity(activity)
            criteria.append(criterion)
        return query, criteria

    def query_filter_by_activity(self, activity):
        if activity is not None:
            activity_name = self.query_filter_by_activity_name(activity)
            if activity_name is None:
                # "Activity name must not be None."
                # (lb): This seems like a tedious branch to test and support. Same
                # goes for `activity is None` (the last else branch of this method).
                # Furthermore, the CLI does not let the user query for Activity
                # where name is None. Though at least the QueryTerms support
                # setting Activity=None (which is the last else branch of the
                # outer if-block). But as far as passing an Activity object to this
                # method, there's no production code that does that; you'd only
                # get here from a new test. Or maybe for some reason wiring
                # this path for some new feature.
                criterion = (AlchemyActivity.pk == activity.pk)
            else:
                # NOTE: Strict name matching, case and exactness.
                #       Not, say, func.lower(name) == func.lower(...),
                #       or using sqlalchemy ilike().
                criterion = (AlchemyActivity.name == activity_name)
        else:
            # activity is None.
            # (lb): Note that there's no production path that'll bring execution here.
            # - MAYBE: See preceding long comment: Add test; maybe wire from CLI.
            #   But what's the use case? You can find nameless Activities with `-a ''`.
            #   And there shouldn't be any Facts where Activity is NONE, right?
            #   Only unnamed Activities, and there's only at most one of those.
            criterion = (AlchemyFact.activity == None)  # noqa: E711
        return criterion

    def query_filter_by_activity_name(self, activity):
        activity_name = None
        try:
            if not activity.pk:
                activity_name = activity.name
        except AttributeError:
            activity_name = activity
        return activity_name

    # ***

    def query_filter_by_categories(self, query, qt):
        query, criteria = self.query_criteria_filter_by_categories(query, qt)
        query = query.filter(or_(*criteria))
        return query

    def query_criteria_filter_by_categories(self, query, qt):
        criteria = []
        for category in qt.match_categories or []:
            criterion = self.query_filter_by_category(category)
            criteria.append(criterion)
        return query, criteria

    def query_filter_by_category(self, category):
        if category is not None:
            category_name = self.query_filter_by_category_name(category)
            if category_name is None:
                # See comment in query_filter_by_activity: this path not
                # reachable via production code.
                criterion = (AlchemyCategory.pk == category.pk)
            else:
                # NOTE: Strict name matching. Case and exactness count.
                criterion = (AlchemyCategory.name == category_name)
        else:
            # (lb): I tried to avoid delinting (the noqa) using is_, e.g.,
            #   criterion = (AlchemyActivity.category.is_(None))
            # but didn't happen:
            #   *** NotImplementedError: <function is_ at 0x7f75030f0280>
            criterion = (AlchemyActivity.category == None)  # noqa: E711
        return criterion

    def query_filter_by_category_name(self, category):
        category_name = None
        try:
            if not category.pk:
                category_name = category.name
        except AttributeError:
            category_name = category
        return category_name

    # ***

    def query_filter_by_tags(self, query, qt):
        # Note this method call only for Facts.get_all, but not other items' get_all.
        criteria = self.query_criteria_filter_by_tags(qt)
        query = query.filter(or_(*criteria))
        return query

    def query_criteria_filter_by_tags(self, qt):
        criteria = []
        for tag in qt.match_tags or []:
            criterion = self.query_filter_by_tag(tag)
            criteria.append(criterion)
        return criteria

    def query_filter_by_tag(self, tag):
        if tag is not None:
            tag_name = self.query_filter_by_tag_name(tag)
            if tag_name is None:
                # See comment in query_filter_by_activity: this path not
                # reachable via production code.
                criterion = (AlchemyTag.pk == tag.pk)
            else:
                criterion = (AlchemyTag.name == tag_name)
        else:
            # tag is None.
            criterion = (AlchemyFact.tags == None)  # noqa: E711
        return criterion

    def query_filter_by_tag_name(self, tag):
        tag_name = None
        try:
            if not tag.pk:
                tag_name = tag.name
        except AttributeError:
            tag_name = tag
        return tag_name

    # ***

    def query_order_by_sort_cols(self, query, query_terms, has_facts, *agg_cols):
        for idx, sort_col in enumerate(query_terms.sort_cols or []):
            direction = query_sort_order_at_index(query_terms.sort_orders, idx)
            query = self.query_order_by_sort_col(
                query, query_terms, sort_col, direction, has_facts, *agg_cols,
            )
        return query

    def query_order_by_sort_col(
        self,
        query,
        query_terms,
        sort_col,
        direction,
        has_facts,
        # The following columns are specific to Activity, Category, and Tag
        # gather() calls. The FactManager.gather overrides query_order_by_sort_col
        # to pass its own specific query columns.
        count_col=None,
        time_col=None,
    ):
        # Get the 'name' sort column, e.g., 'activity', 'category', or 'tag'.
        name_col = self._gather_query_order_by_name_col
        return self.query_usage_order_by(
            query,
            sort_col,
            direction,
            has_facts,
            name_col=name_col,
            count_col=count_col,
            time_col=time_col,
        )

    def query_usage_order_by(
        self,
        query,
        sort_col,
        direction,
        has_facts,
        name_col,
        count_col=None,
        time_col=None,
    ):
        # The query builder is responsible for ensuring that columns necessary
        # for the specified sort are included in the query. So this method can
        # assume that the necessary table (such as Fact, for order_by_start)
        # or aggregate columns (such as count_col or time_col) are available
        # when required for the sort.
        order_cols = []
        check_agg = False
        if sort_col == 'start':
            assert has_facts
            order_cols = self.cols_order_by_start(query)
        elif sort_col == 'usage':
            order_cols = [count_col]
            check_agg = True
        elif sort_col == 'time':
            order_cols = [time_col]
            check_agg = True
        elif (
            sort_col == 'activity'
            or (name_col == 'activity' and (sort_col == 'name' or not sort_col))
        ):
            order_cols = [AlchemyActivity.name]
        elif (
            sort_col == 'category'
            or (name_col == 'category' and (sort_col == 'name' or not sort_col))
        ):
            order_cols = [AlchemyCategory.name]
        elif (
            sort_col == 'tag'
            or (name_col == 'tag' and (sort_col == 'name' or not sort_col))
        ):
            if self._gather_query_order_by_name_col == 'tag':
                order_cols = [AlchemyTag.name]
            else:
                # Print a warning if called on Activity.get_all or Category.get_all,
                # because we don't join the Tag table for either of those.
                check_agg = True

        if not order_cols and check_agg:
            self.store.logger.warning("Invalid sort_col: {}".format(sort_col))
        elif not order_cols:
            self.store.logger.warning("Unknown sort_col: {}".format(sort_col))
        else:
            query = self.query_order_by_cols(query, direction, order_cols)
        return query

    # ***

    def cols_order_by_start(self, query):
        # Include end so that momentaneous Facts are sorted properly.
        # - And add PK, too, so momentaneous Facts are sorted predictably.
        return [AlchemyFact.start, AlchemyFact.end, AlchemyFact.pk]

    def query_order_by_start(self, query, direction):
        order_cols = self.cols_order_by_start(query)
        query = self.query_order_by_cols(query, direction, order_cols)
        return query

    def query_order_by_cols(self, query, direction, order_cols):
        directional_cols = [direction(col) for col in order_cols]
        query = query.order_by(*directional_cols)
        return query

    # ***

    def query_prepared_trace(self, query):
        if self.store.config['dev.catch_errors']:
            # 2020-05-21: I don't generally like more noise in my tmux dev environment
            # logger pane, but I do like seeing the query, especially with all the
            # recent gather() development (improved grouping, sorting, and aggregates).
            logf = self.store.logger.warning
        else:
            logf = self.store.logger.debug
        logf('Query: {}'.format(str(query)))

    # ***

    def query_process_results(
        self,
        records,
        raw,
        include_stats,
        requested_usage,
    ):
        def _query_process_results(records):
            if not records or not include_stats:
                return _process_records_items_only(records)
            return _process_records_items_and_aggs(records)

        def _process_records_items_only(records):
            if not raw:
                return [_as_hamster_or_none(item) for item in records]
            return records

        def _process_records_items_and_aggs(records):
            if not raw:
                return _process_records_items_and_aggs_hydrate(records)
            return records

        def _process_records_items_and_aggs_hydrate(records):
            if requested_usage:
                return [(_as_hamster_or_none(item), *cols) for item, *cols in records]
            return [_as_hamster_or_none(item) for item, *cols in records]

        def _as_hamster_or_none(item):
            # If query used outer join, and if, say, a Fact has an Activity set NULL,
            # or if an Activity has a Category set NULL, return None for the item.
            if item is not None:
                return item.as_hamster(self.store)
            return None

        return _query_process_results(records)

    # ***

# ***

