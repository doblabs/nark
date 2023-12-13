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

"""Query class module."""

from collections import namedtuple

QueryTermsTuple = namedtuple('QueryTermsTuple', (
    'raw',
    'named_tuples',
    'include_stats',
    'count_results',
    'key',
    'since',
    'until',
    'endless',
    'exclude_ongoing',
    'partial',
    'deleted',
    'search_terms',
    'broad_match',
    'match_activities',
    'match_categories',
    'match_tags',
    'group_activity',
    'group_category',
    'group_tags',
    'group_days',
    'sort_cols',
    'sort_orders',
    'limit',
    'offset',
))


class QueryTerms(object):
    """
    The QueryTerms encapsulate all the input and output parameters of an item lookup.

    This class is a standalone class so that it's easy for frontends to use, too.
    """

    def __init__(self, **kwargs):
        self.setup_terms(**kwargs)

    def __str__(self):
        return ' / '.join([
            'raw?: {}'.format(self.raw),
            'named?: {}'.format(self.named_tuples),
            'stats?: {}'.format(self.include_stats),
            'count?: {}'.format(self.count_results),
            'key: {}'.format(self.key),
            'since: {}'.format(self.since),
            'until: {}'.format(self.until),
            'endless: {}'.format(self.endless),
            'excl-ongo?: {}'.format(self.exclude_ongoing),
            'partial: {}'.format(self.partial),
            'del?: {}'.format(self.deleted),
            'terms: {}'.format(self.search_terms),
            'broad: {}'.format(self.broad_match),
            'acts: {}'.format(self.match_activities),
            'cats: {}'.format(self.match_categories),
            'tags: {}'.format(self.match_tags),
            'grp-acts?: {}'.format(self.group_activity),
            'grp-cats?: {}'.format(self.group_category),
            'grp-tags?: {}'.format(self.group_tags),
            'grp-days?: {}'.format(self.group_days),
            'cols: {}'.format(self.sort_cols),
            'ords: {}'.format(self.sort_orders),
            'limit: {}'.format(self.limit),
            'offset: {}'.format(self.offset),
        ])

    def setup_terms(
        self,

        raw=False,
        named_tuples=False,
        include_stats=None,

        count_results=False,

        key=None,
        since=None,
        until=None,

        # - SPIKE: (lb): Are 'endless' and 'exclude_ongoing' just opposites?
        endless=False,
        # - Use exclude_ongoing to omit the final, active Fact, if any,
        #   from the results.
        exclude_ongoing=None,

        partial=False,

        # The `deleted` option only applies to Facts.
        deleted=False,

        search_terms=None,
        broad_match=False,

        # - Note that item name matching is strict -- case and exactness count.
        match_activities=[],
        match_categories=[],
        match_tags=[],
        # - MEH: (lb): For parity, could add a 'tags' option to restrict the
        #   search to Activities used on Facts with specific 'tags', but how
        #   complicated and useless does that sound.

        # - Use the group_* flags to GROUP BY specific attributes.
        group_activity=False,
        group_category=False,
        group_tags=False,
        group_days=False,

        # - (lb): I added grouping support to FactManager.get_all via the options:
        #     group_activity
        #     group_category
        #     group_tags
        #   We could add them to this query, but it'd make it much more complex,
        #   and you'd get essentially the same results as using Fact.get_all (save
        #   for any Activities that are not applied to any Facts, but we can live
        #   with that gap in support). (tl;dr, use `dob list fact` or `dob usage fact`
        #   to group query results, and use the --column option if you want to tweak
        #   the output report columns, e.g., to match this method's output.)

        sort_cols=None,
        sort_orders=None,

        limit=None,
        offset=None
    ):
        """
        Configures query parameters for item.get_all() and item.get_all_by_usage().

        Some of the settings affect the query, and some affect the returned results.

        Each of the query parameters is optional. Defaults are such that each
        argument default is falsey: it's either False, None, or an empty list.

        Args:
            raw: If True, returns 'raw' SQLAlchemy items (e.g., AlchemyFact).
                If False, returns first-class nark objects (e.g., Fact).
            named_tuples: If True, each result is a attribute-accessible tuple
                (like a namedtuple). If False, each result is a simple list. In
                either case, the first entry in always the item, and the order
                of additional details is always the same.
            include_stats: If True, computes additional details for each item or set
                of grouped items, and returns a list of tuples (with the item or
                aggregated item as the first element). Otherwise, if False, returns
                a list of matching items only. For Attribute, Category, and Tag
                queries, enable include_stats to receive a count of Facts that use
                the item, as well as the cumulative duration (end - start) of those
                Facts. For Facts, includes additional aggregate details.

            count_results: If True, return only a count of query matches (an integer).
                By default, count_results is False, and the method returns a list of
                results (of either items or tuples, depending on include_stats).

            key: If specified, look for an item with this PK. See also the get()
                method, if you do not need aggregate results.
            since: Restrict Facts to those that start at or after this time.
            until: Restrict Facts to those that end at or before this time.
                Note that a query will *not* match any Facts that start before and
                end after (e.g. that span more than) the specified timeframe.

            endless: If True, include the active Fact, if any, in the query.
            exclude_ongoing: If True, excldues the active Fact, in any.
            partial: If True, restrict Facts to those that start or end within the
                since-to-until time window.
            deleted: If True, include items marked 'deleted'.
            search_terms (None, or str list): Use to restrict to items whose name
                matches any on the specified search terms. Each comparison is case
                insensitive, and the match can occur in the middle of a string. If
                an item name matches one or more of the search terms, if any, it
                will be included in the results.
                * Use ``not`` before a search term to exclude its matches from the
                  results.
            broad_match: If True, apply search_terms fuzzy search to activity,
                category, and tag names.

            match_activities (list of items, each a nark.Activity, str, or None;
                optional): Matches only Activity(ies) or Facts that use the
                indicated Activity(ies) or Activity name(s) (exactly matched).
                The activity name can be specified as a string, or by passing a
                ``nark.Activity`` object whose name will be used. To match Facts
                without an Activity assigned, use ``None``. If ``match_activities``
                contains more than one item, Activities that exactly match or
                Facts that use *any* of the specified Activities will be included.
            match_categories (list of items, each a nark.Category, str, or None;
                optional): Matches only Category(ies) or Facts that use Activities
                that use the indicated Category(ies) or Category name(s) (exactly
                matched). The category name can be specified as a string, or by
                passing a ``nark.Category`` object whose name will be used. To match
                Facts with an Activity that does not have a Category assigned, use
                ``None``. If ``match_categories`` contains more than one item,
                Categories that exactly match or Facts that use an Activity with
                *any* of the specified Categories will be included.
            match_tags (list of items, each a nark.Tag, str, or None; optional):
                Matchies only Tag(s) or Facts that use the indicated Tag(s) or
                Tag name(s) (exactly matched). The tag name can be specified as
                a string, or by passing a ``nark.Tag`` object whose name will be
                used. To match Facts without a Tag assigned, use ``tag=None``.
                If ``match_tags`` contains more than one item, Tags that exactly
                match or Facts that use an Tag with *any* of the specified Tags
                will be included.

            group_activity: If True, GROUP BY the Activity name, unless group_category
                is also True, then GROUP BY the Activity PK and the Category PK.
            group_category: If True, GROUP BY the Category PK.
            group_tags: If True, group by the Tag PK.
            group_days: If True, group by the Fact start date (e.g., 1999-12-31,
                i.e., truncating clock time).

            sort_cols (str list, optional): Which column(s) to sort by.
                - If not aggregating results, defaults to 'name' and orders
                  by item name.
                - When aggregating results (include_stats=True) or searching
                  Facts, defaults to 'start', and orders results by Fact start.
                - Choices include: 'start', 'time', 'day', 'name', 'activity,
                  'category', 'tag', 'usage', and 'fact'.
                - Note that 'start' and 'usage' only apply if include_stats,
                  and 'day' is only valid when group_days is True.
            sort_orders (str list, optional): Specifies the direction of each
                sort specified by sort_cols. Use the string 'asc' or 'desc'
                in the corresponding index of sort_orders that you want applied
                to the corresponding entry in soft_cols. If there is no
                corresponding entry in sort_orders for a specific sort_cols
                entry, that sort column is ordered in ascending order.

            limit (int, optional): Query "limit".
            offset (int, optional): Query "offset".
        """
        self.raw = raw
        self.named_tuples = named_tuples
        self.include_stats = include_stats

        self.count_results = count_results

        self.key = key
        self.since = since
        self.until = until
        self.endless = endless
        self.exclude_ongoing = exclude_ongoing
        self.partial = partial
        self.deleted = deleted

        self.search_terms = search_terms
        self.broad_match = broad_match

        self.match_activities = match_activities
        self.match_categories = match_categories
        self.match_tags = match_tags

        self.group_activity = group_activity
        self.group_category = group_category
        self.group_tags = group_tags
        self.group_days = group_days

        self.sort_cols = sort_cols
        self.sort_orders = sort_orders

        self.limit = limit
        self.offset = offset

    # ***

    def as_tuple(self):
        return QueryTermsTuple(
            raw=self.raw,
            named_tuples=self.named_tuples,
            include_stats=self.include_stats,
            count_results=self.count_results,
            key=self.key,
            since=self.since,
            until=self.until,
            endless=self.endless,
            exclude_ongoing=self.exclude_ongoing,
            partial=self.partial,
            deleted=self.deleted,
            search_terms=self.search_terms,
            broad_match=self.broad_match,
            match_activities=self.match_activities,
            match_categories=self.match_categories,
            match_tags=self.match_tags,
            group_activity=self.group_activity,
            group_category=self.group_category,
            group_tags=self.group_tags,
            group_days=self.group_days,
            sort_cols=self.sort_cols,
            sort_orders=self.sort_orders,
            limit=self.limit,
            offset=self.offset,
        )

    def __eq__(self, other):
        if other is not None and not isinstance(other, QueryTermsTuple):
            other = other.as_tuple()
        return self.as_tuple() == other

    # ***

    @property
    def is_grouped(self):
        is_grouped = (
            self.group_activity
            or self.group_category
            or self.group_tags
            or self.group_days
        )
        return is_grouped

    def sort_cols_has_any(self, *args):
        return set(self.sort_cols or []).intersection(set(args))

    @property
    def sorts_cols_has_stat(self):
        return self.sort_cols_has_any('usage', 'time', 'day')

