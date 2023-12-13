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

import datetime

from . import BaseManager
from ..helpers import fact_time
from ..items.fact import Fact


class BaseFactManager(BaseManager):
    """Base class defining the minimal API for a FactManager implementation."""
    def __init__(self, *args, localize=False, **kwargs):
        super(BaseFactManager, self).__init__(*args, **kwargs)
        # All for one, and one for all, set class-wide behavior.
        Fact.localize(localize)

    # ***

    def save(self, fact, **kwargs):
        """
        Save a Fact to our selected backend.

        Unlike the private ``_add`` and ``_update`` methods, ``save``
        requires that the config given ``fact_min_delta`` is enforced.

        Args:
            fact (nark.Fact): Fact to be saved. Needs to be complete otherwise
            this will fail.

        Returns:
            nark.Fact: Saved Fact.

        Raises:
            ValueError: If ``fact.delta`` is smaller than
              ``self.config['time.fact_min_delta']``
        """
        def _save():
            enforce_fact_min_delta()
            return super(BaseFactManager, self).save(
                fact, cls=Fact, named=False, **kwargs
            )

        def enforce_fact_min_delta():
            # BROKEN/DONT_CARE: (lb): The Facts Carousel does not check the
            # min delta, meaning you could violate fact_min_delta and end up
            # raising from herein. Oh, well, I don't delta, so I don't care.
            if not fact.end:
                # The ongoing, active fact.
                return

            fact_min_delta = int(self.config['time.fact_min_delta'])
            if not fact_min_delta:
                # User has not enabled min-delta behavior.
                return

            min_delta = datetime.timedelta(seconds=fact_min_delta)
            if fact.delta() >= min_delta:
                # Fact is at least as long as user's min-delta.
                return

            message = _(
                "The Fact duration is shorter than the mandatory value of "
                "{} seconds specified in your config.".format(fact_min_delta)
            )
            self.store.logger.error(message)
            raise ValueError(message)

        return _save()

    # ***

    def _add(self, fact):
        """
        Add a new ``Fact`` to the backend.

        Args:
            fact (nark.Fact): Fact to be added.

        Returns:
            nark.Fact: Added ``Fact``.

        Raises:
            ValueError: If passed fact has a PK. New facts should not have one.
            ValueError: If time window is already occupied.
        """
        raise NotImplementedError

    # ***

    def _update(self, fact):
        """
        Update and existing fact with new values.

        Args:
            fact (nark.fact): Fact instance holding updated values.

        Returns:
            nark.fact: Updated Fact

        Raises:
            KeyError: if a Fact with the relevant PK could not be found.
            ValueError: If the the passed activity does not have a PK assigned.
            ValueError: If the time window is already occupied.
        """
        raise NotImplementedError

    # ***

    def remove(self, fact, purge=False):
        """
        Remove a given ``Fact`` from the backend.

        Args:
            fact (nark.Fact): ``Fact`` instance to be removed.

        Returns:
            bool: Success status

        Raises:
            ValueError: If fact passed does not have an pk.
            KeyError: If the ``Fact`` specified could not be found in the backend.
        """
        raise NotImplementedError

    # ***

    def get(self, pk, deleted=None):
        """
        Return a Fact by its primary key.

        Args:
            pk (int): Primary key of the ``Fact to be retrieved``.

            deleted (boolean, optional): False to restrict to non-deleted
                Facts; True to find only those marked deleted; None to find
                all.

        Returns:
            nark.Fact: The ``Fact`` corresponding to the primary key.

        Raises:
            KeyError: If primary key not found in the backend.
        """
        raise NotImplementedError

    # ***

    # Note that get_all() is implemented, by the BaseManager, so it can
    # wrap the 'since' and 'until' inputs, and convert them to datatime
    # objects, before calling gather(), which is implemented by the
    # backends.sqlalchemy.managers GatherFactManager.

    # ***

    def get_all_by_usage(self, query_terms=None, **kwargs):
        """
        Similar to get_all(), but include count of Facts that reference each Activity.
        """
        raise NotImplementedError

    # ***

    def gather(self, query_terms):
        """
        Return a list of ``Facts`` matching given criteria.
        """
        raise NotImplementedError

    # ***

    def get_today(self):
        """
        Return all facts for today, while respecting ``day_start``.

        Returns:
            list: List of ``Fact`` instances.

        Note:
            * This only returns completed facts and does not include the
                active Fact, whether or not it exists.
        """
        self.store.logger.debug(_("Returning today's facts"))

        today = self.store.now.date()
        since = datetime.datetime.combine(today, self.config['time.day_start'])
        until = self.day_end_datetime(today)
        return self.get_all(since=since, until=until)

    def day_end_datetime(self, end_date=None):
        if end_date is None:
            end_date = self.store.now.date()
        start_time = self.config['time.day_start']
        return fact_time.day_end_datetime(end_date, start_time)

    # ***

    # 2020-01-28: This method only called by nark/tests/. dob replaced its
    # stop-fact mechanism with add_fact, to handle all the possible stop
    # scenarios (e.g., specifying an end time or not; appending the endless
    # fact's description, if it's already got one, etc.).
    def stop_current_fact(self, end_hint=None):
        """
        Stop current 'active fact'.

        Args:
            end_hint (datetime.timedelta or datetime.datetime, optional): Hint to be
                considered when setting ``Fact.end``. If no hint is provided
                ``Fact.end`` will be ``datetime.datetime.now()``. If a ``datetime`` is
                provided, this will be used as ``Fact.end`` value. If a ``timedelta``
                is provided it will be added to ``datetime.datetime.now()``.
                If you want the computed ``end`` to be *before* ``now()``
                you can pass negative ``timedelta`` values. Defaults to None.

        Returns:
            nark.Fact: The stored fact.

        Raises:
            TypeError: If ``end_hint`` is not a ``datetime.datetime`` or
                ``datetime.timedelta`` instance or ``None``.
            ValueError: If there is no currently 'active fact' present.
            ValueError: If the final end value (due to the hint) is before
                the fact's start value.
        """
        self.store.logger.debug(_("Stopping 'active fact'."))

        if not (
            (end_hint is None)
            or isinstance(end_hint, datetime.datetime)
            or isinstance(end_hint, datetime.timedelta)
        ):
            raise TypeError(_(
                "The 'end_hint' you passed needs to be either a"
                "'datetime.datetime' or 'datetime.timedelta' instance."
            ))

        if end_hint:
            if isinstance(end_hint, datetime.datetime):
                end = end_hint
            else:
                end = self.store.now + end_hint
        else:
            end = self.store.now

        # Note that get_current_fact raises KeyError if no Active Fact.
        fact = self.get_current_fact()

        if fact.start > end:
            raise ValueError(_(
                'Cannot end the Fact before it started.'
                ' Try editing the Fact instead.'
            ))
        else:
            fact.end = end
        new_fact = self.save(fact)

        self.store.logger.debug(_("Current fact is now history!"))

        return new_fact

    # ***

    def get_current_fact(self):
        """
        Provide a way to retrieve any existing 'ongoing fact'.

        Returns:
            nark.Fact: An instance representing the <active fact>.

        Raises:
            KeyError: If no ongoing fact is present.
        """
        def _get_current_fact():
            self.store.logger.debug(_("Looking for the 'active fact'."))
            # See alternatively:
            #   facts = self.get_all(endless=True)
            facts = self.endless()
            ensure_one_or_fewer_ongoing(facts)
            ensure_one_or_more_ongoing(facts)
            return facts[0]

        def ensure_one_or_fewer_ongoing(facts):
            if len(facts) <= 1:
                return
            msg = '{} IDs: {}'.format(
                _('More than 1 ongoing Fact found. Your database is whacked out!!'),
                ', '.join([str(fact.pk) for fact in facts]),
            )
            self.store.logger.debug(msg)
            raise Exception(msg)

        def ensure_one_or_more_ongoing(facts):
            if facts:
                return
            # See also: NO_ACTIVE_FACT_HELP
            message = _("No active Fact found.")
            self.store.logger.debug(message)
            raise KeyError(message)

        return _get_current_fact()

    # ***

    def find_latest_fact(self, restrict=None):
        assert not restrict or restrict in ['ended', 'ongoing', ]
        fact = None
        if not restrict or restrict == 'ongoing':
            try:
                fact = self.get_current_fact()
            except KeyError:
                fact = None
            except Exception:
                # (lb): Unexpected! This could mean more than one ongoing Fact found!
                raise
        if fact is None and restrict != 'ongoing':
            results = self.get_all(
                sort_cols=('start',),
                sort_orders=('desc',),
                limit=1,
                exclude_ongoing=True,
                # Just to be clear, we want just the Facts.
                include_stats=False,
            )
            if len(results) > 0:
                assert len(results) == 1
                # (lb) Silly, since 2018-06-28 I had `fact, = results`.
                # Was I trying to be clever? Indexing seems more readable.
                fact = results[0]
        return fact

    # ***

    def find_oldest_fact(self):
        fact = None
        results = self.get_all(
            sort_cols=('start',),
            sort_orders=('asc',),
            limit=1,
        )
        if len(results) > 0:
            assert len(results) == 1
            fact = results[0]
        return fact

    # ***

    def cancel_current_fact(self, purge=False):
        """
        Delete the current, ongoing, endless, active Fact.
        (Really just mark it deleted.)

        Returns:
            None: If everything worked as expected.

        Raises:
            KeyError: If no ongoing, active fact found.
        """
        self.store.logger.debug(_("Cancelling 'active fact'."))
        # Note that get_current_fact raises KeyError if no Active Fact.
        fact = self.get_current_fact()
        self.remove(fact, purge)
        return fact

    # ***

    def starting_at(self, fact):
        """
        Return the fact starting at the moment in time indicated by fact.start.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``start`` set.

        Returns:
            nark.Fact: The found Fact, or None if none found.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError

    # ***

    def ending_at(self, fact):
        """
        Return the fact ending at the moment in time indicated by fact.end.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``end`` set.

        Returns:
            nark.Fact: The found Fact, or None if none found.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError

    # ***

    def antecedent(self, fact=None, ref_time=None):
        """
        Return the Fact immediately preceding the indicated Fact.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``start`` set.

            ref_time (datetime.datetime):
                In lieu of fact, pass the datetime to reference.

        Returns:
            nark.Fact: The antecedent Fact, or None if none found.

        Raises:
            ValueError: If neither ``start`` nor ``end`` is set on fact.
        """
        raise NotImplementedError

    # ***

    def subsequent(self, fact=None, ref_time=None):
        """
        Return the Fact immediately following the indicated Fact.

        Args:
            fact (nark.Fact):
                The Fact to reference, with its ``end`` set.

            ref_time (datetime.datetime):
                In lieu of fact, pass the datetime to reference.

        Returns:
            nark.Fact: The subsequent Fact, or None if none found.

        Raises:
            ValueError: If neither ``start`` nor ``end`` is set on fact.
        """
        raise NotImplementedError

    # ***

    def strictly_during(self, start, end, result_limit=1000):
        """
        Return the fact(s) strictly contained within a start and end time.

        Args:
            start (datetime.datetime):
                Start datetime of facts to find.

            end (datetime.datetime):
                End datetime of facts to find.

            result_limit (int):
                Maximum number of facts to find, else log warning message.

        Returns:
            list: List of ``nark.Facts`` instances.
        """
        raise NotImplementedError

    # ***

    def surrounding(self, fact_time):
        """
        Return the fact(s) at the given moment in time.
        Note that this excludes a fact that starts or ends at this time.
        (See antecedent and subsequent for finding those facts.)

        Args:
            fact_time (datetime.datetime):
                Time of fact(s) to match.

        Returns:
            list: List of ``nark.Facts`` instances.

        Raises:
            IntegrityError: If more than one Fact found at given time.
        """
        raise NotImplementedError

    # ***

    def endless(self):
        """
        Return any facts without a fact.start or fact.end.

        Args:
            <none>

        Returns:
            list: List of ``nark.Facts`` instances.
        """
        raise NotImplementedError

