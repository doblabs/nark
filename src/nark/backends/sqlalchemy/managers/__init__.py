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

"""Shared storage object manager utility functions."""

from sqlalchemy import asc, desc

__all__ = (
    'query_apply_limit_offset',
    'query_apply_true_or_not',
    'query_prepare_datetime',
    'query_sort_order_at_index',
)


def query_apply_limit_offset(query, limit=None, offset=None):
    """
    Applies 'limit' and 'offset' to the database fetch query

    On applies 'limit' if specified; and only applies 'offset' if specified.

    Args:
        query (???): Query (e.g., return from self.store.session.query(...))

        kwargs (keyword arguments):
            limit (int|str, optional): Limit to apply to the query.

            offset (int|str, optional): Offset to apply to the query.

    Returns:
        list: The query passed in, possibly updated with limit and/or offset.
    """
    if limit and limit > 0:
        query = query.limit(limit)
    if offset and offset > 0:
        query = query.offset(offset)
    return query


def query_apply_true_or_not(query, column, condition):
    if condition is not None:
        return query.filter(column == condition)
    return query


def query_sort_order_at_index(sort_orders, idx):
    try:
        direction = desc if sort_orders and sort_orders[idx] == 'desc' else asc
    except IndexError:
        direction = asc
    return direction


def query_prepare_datetime(datetm):
    # Be explicit with the format used by the SQL engine, otherwise,
    #   e.g., and_(AlchemyFact.start > start) might match where
    #   AlchemyFact.start == start. In the case of SQLite, the stored
    #   date will be translated with the seconds, even if 0, e.g.,
    #   "2018-06-29 16:32:00", but the datetime we use for the compare
    #   gets translated without, e.g., "2018-06-29 16:32". And we
    #   all know that "2018-06-29 16:32:00" > "2018-06-29 16:32".
    # See also: func.datetime(AlchemyFact.start/end).
    cmp_fmt = '%Y-%m-%d %H:%M:%S'
    text = datetm.strftime(cmp_fmt)
    return text

