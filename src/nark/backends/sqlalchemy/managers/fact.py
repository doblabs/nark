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

from datetime import datetime

from sqlalchemy import asc, desc, func
from sqlalchemy.sql.expression import and_, or_

from ..objects import AlchemyFact
from . import query_apply_true_or_not, query_prepare_datetime
from .gather_fact import GatherFactManager

__all__ = ("FactManager",)


class FactManager(GatherFactManager):
    """ """

    def __init__(self, *args, **kwargs):
        super(FactManager, self).__init__(*args, **kwargs)

    # ***

    def _add(self, fact, raw=False, skip_commit=False, ignore_pks=[]):
        """
        Add a new fact to the database.

        Args:
            fact (nark.Fact): Fact to be added.
            raw (bool): If ``True`` return ``AlchemyFact`` instead.

        Returns:
            nark.Fact: Fact as stored in the database

        Raises:
            ValueError: If the passed fact has a PK assigned.
                New facts should not have one.

            ValueError: If the time window is already occupied.
        """
        self.adding_item_must_not_have_pk(fact)

        self.must_validate_datetimes(fact, ignore_pks=ignore_pks)

        alchemy_fact = AlchemyFact(
            pk=None,
            activity=None,
            # FIXME/2018-08-23 00:38: Is this still valid?
            # FIXME: mircoseconds are being stored...
            #        I modified fact_time.must_be_datetime_or_relative to strip
            #        milliseconds. but they're still being saved (just as six 0's).
            start=fact.start,
            end=fact.end,
            description=fact.description,
            deleted=bool(fact.deleted),
            split_from=fact.split_from,
        )
        get_or_create = self.store.activities.get_or_create
        alchemy_fact.activity = get_or_create(fact.activity, raw=True, skip_commit=True)
        tags = [
            self.store.tags.get_or_create(tag, raw=True, skip_commit=True)
            for tag in fact.tags
        ]
        alchemy_fact.tags = tags

        result = self.add_and_commit(
            alchemy_fact,
            raw=raw,
            skip_commit=skip_commit,
        )

        return result

    # ***

    def _update(self, fact, raw=False, ignore_pks=[]):
        """
        Update and existing fact with new values.

        Args:
            fact (nark.fact): Fact instance holding updated values.

            raw (bool): If ``True`` return ``AlchemyFact`` instead.
              ANSWER: (lb): "instead" of what? raw is not used by Fact...

        Returns:
            nark.fact: Updated Fact

        Raises:
            KeyError: if a Fact with the relevant PK could not be found.
            ValueError: If the the passed activity does not have a PK assigned.
            ValueError: If the time window is already occupied.
        """
        self.store.logger.debug("Received: {!r} / raw: {}".format(fact, raw))

        if not fact.pk:
            message = _(
                "The Fact passed ('{!r}') does not have a PK."
                " We do not know which entry to modify."
            ).format(fact)
            self.store.logger.error(message)
            raise ValueError(message)

        self.must_validate_datetimes(fact, ignore_pks=ignore_pks)

        alchemy_fact = self.store.session.query(AlchemyFact).get(fact.pk)
        if not alchemy_fact:
            message = _("No Fact with PK ‘{}’ was found.").format(fact.pk)
            self.store.logger.error(message)
            raise KeyError(message)

        if alchemy_fact.deleted:
            message = _("Cannot edit deleted Fact: ‘{!r}’.".format(fact))
            self.store.logger.error(message)
            raise ValueError(message)

        if (
            (fact.deleted and (fact.end == alchemy_fact.end))
            or (fact.end and not alchemy_fact.end)
        ) and fact.equal_sans_end(alchemy_fact):
            # Don't bother with split_from entry.
            # MAYBE: (lb): Go full wiki and store edit times? Ug...
            new_fact = alchemy_fact
            alchemy_fact.deleted = fact.deleted
            alchemy_fact.end = fact.end
        else:
            assert alchemy_fact.pk == fact.pk
            was_split_from = fact.split_from
            fact.split_from = alchemy_fact
            # Clear the ID so that a new ID is assigned.
            fact.pk = None
            new_fact = self._add(
                fact, raw=True, skip_commit=True, ignore_pks=ignore_pks
            )
            # NOTE: _add() calls:
            #       self.store.session.commit()
            # The fact being split from is deleted/historic.
            alchemy_fact.deleted = True
            assert new_fact.pk > alchemy_fact.pk
            # Restore the ID to not confuse the caller!
            # The caller will still have a handle on Fact. Rather than
            # change its pk to new_fact's, have it reflect its new
            # split_from status.
            fact.pk = alchemy_fact.pk
            fact.split_from = was_split_from
            # The `alchemy_fact` is what gets saved, but the `fact`
            # is what the caller passed us, so update it, too.
            fact.deleted = True

        self.store.session.commit()

        self.store.logger.debug("Updated: {!r}".format(fact))

        if not raw:
            new_fact = new_fact.as_hamster(self.store)

        return new_fact

    # ***

    def must_validate_datetimes(self, fact, ignore_pks=[]):
        if not isinstance(fact.start, datetime):
            raise TypeError(_("Missing start time for ‘{!r}’.").format(fact))

        # Check for valid time range.
        invalid_range = False
        if fact.end is not None:
            if fact.start > fact.end:
                invalid_range = True
            else:
                # EXPERIMENTAL: Sneaky, "hidden", vacant, timeless Facts.
                allow_momentaneous = self.store.config["time.allow_momentaneous"]
                if not allow_momentaneous and fact.start >= fact.end:
                    invalid_range = True

        if invalid_range:
            message = _("Invalid time range for “{!r}”.").format(fact)
            if fact.start == fact.end:  # pragma: no cover
                assert False  # (lb): Preserved in case we revert == policy.
                message += _(" The start time cannot be the same as the end time.")
            else:
                message += _(" The start time cannot be after the end time.")
            self.store.logger.error(message)
            raise ValueError(message)

        if not self._timeframe_available_for_fact(fact, ignore_pks):
            msg = _(
                "One or more Facts already exist "
                "between the indicated start and end times. "
            )
            self.store.logger.error(msg)
            raise ValueError(msg)

    # ***

    def _timeframe_available_for_fact(self, fact, ignore_pks=[]):
        """
        Determine if a timeframe given by the passed fact is already occupied.

        This method takes also such facts into account that start before and end
        after the fact in question. In that regard it exceeds what ``gather``
        would return.

        Args:
            fact (Fact): The fact to check. Please note that the fact is expected to
                have a ``start`` and ``end``.

        Returns:
            bool: ``True`` if the timeframe is available, ``False`` if not.

        Note:
            If the given fact is the only fact instance within the given timeframe
            the timeframe is considered available (for this fact)!
        """
        # Use func.datetime and query_prepare_datetime to normalize time comparisons,
        # so that equivalent times that are expressed differently are evaluated
        # as equal, e.g., "2018-01-01 10:00" should match "2018-01-01 10:00:00".
        # FIXME: func.datetime is SQLite-specific: need to abstract for other DBMSes.

        start = query_prepare_datetime(fact.start)
        query = self.store.session.query(AlchemyFact)

        # FIXME: Only use func.datetime on SQLite store.
        #
        #   (lb): SQLite stores datetimes as strings, so what's in the store
        #   might vary depending on, say, changes to this code. As such, some
        #   start and end times might include seconds, and some times might not.
        #   Here we use func.datetime and query_prepare_datetime to normalize the
        #   comparison. But this is SQLite-specific, so we should abstract
        #   the operation for other DBMSes (and probably do nothing, since most
        #   other databases have an actual datetime data type).
        condition = and_(func.datetime(AlchemyFact.end) > start)
        if fact.end is not None:
            end = query_prepare_datetime(fact.end)
            condition = and_(condition, func.datetime(AlchemyFact.start) < end)
        else:
            # The fact is ongoing, so match the ongoing (active) Fact in the store.
            # E711: `is None` breaks Alchemy, so use `== None`.
            condition = or_(AlchemyFact.end == None, condition)  # noqa: E711

        if fact.pk:
            condition = and_(condition, AlchemyFact.pk != fact.pk)

        if fact.split_from:
            condition = and_(condition, AlchemyFact.pk != fact.split_from.pk)

        if ignore_pks:
            condition = and_(condition, AlchemyFact.pk.notin_(ignore_pks))

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        n_found = query.count()

        return not bool(n_found)

    # ***

    def remove(self, fact, purge=False):
        """
        Remove a fact from our internal backend.

        Args:
            fact (nark.Fact): Fact to be removed

        Returns:
            bool: Success status

        Raises:
            ValueError: If fact passed does not have an pk.

            KeyError: If no fact with passed PK was found.
        """
        self.store.logger.debug("Received: {!r}".format(fact))

        if not fact.pk:
            message = _(
                "Fact ‘{!r}’ has no PK. Are you trying to remove a new Fact?"
            ).format(fact)
            self.store.logger.error(message)
            raise ValueError(message)

        alchemy_fact = self.store.session.query(AlchemyFact).get(fact.pk)
        if not alchemy_fact:
            message = _("No Fact with PK ‘{}’ was found.").format(fact.pk)
            self.store.logger.error(message)
            raise KeyError(message)
        if alchemy_fact.deleted:
            message = _("The Fact is already marked deleted.")
            self.store.logger.error(message)
            # FIXME/2018-06-08: (lb): I think we need custom Exceptions...
            raise Exception(message)
        alchemy_fact.deleted = True
        if purge:
            self.store.session.delete(alchemy_fact)
        self.store.session.commit()
        self.store.logger.debug("Deleted: {!r}".format(fact))

    # ***

    def get(self, pk, deleted=None, raw=False):
        """
        Retrieve a fact based on its PK.

        Args:
            pk (int): PK of the fact to be retrieved.

            deleted (boolean, optional):
                False to restrict to non-deleted Facts;
                True to find only those marked deleted;
                None to find all.

            raw (bool): Return the AlchemyActivity instead.

        Returns:
            nark.Fact: Fact matching given PK

        Raises:
            KeyError: If no Fact of given key was found.
        """
        self.store.logger.debug("Received PK: ‘{}’ / raw: {}.".format(pk, raw))

        if deleted is None:
            query = self.store.session.query(AlchemyFact)
            result = query.get(pk)
        else:
            query = self.store.session.query(AlchemyFact)
            query = query.filter(AlchemyFact.pk == pk)
            query = query_apply_true_or_not(query, AlchemyFact.deleted, deleted)
            results = query.all()
            assert len(results) <= 1
            result = results[0] if results else None

        if not result:
            message = _("No Fact with PK ‘{}’ was found.").format(pk)
            self.store.logger.error(message)
            raise KeyError(message)
        if not raw:
            # Explain: Why is as_hamster optionable, when act/cat/tag do it always?
            result = result.as_hamster(self.store)
        self.store.logger.debug("Returning: {!r}".format(result))
        return result

    # ***

    def get_all(self, query_terms=None, lazy_tags=False, **kwargs):
        query_terms, kwargs = self._gather_prepare_query_terms(query_terms, **kwargs)
        if query_terms.sort_cols is None:
            query_terms.sort_cols = ("start",)
        return super(FactManager, self).get_all(
            query_terms, lazy_tags=lazy_tags, **kwargs
        )

    # ***

    def get_all_by_usage(self, query_terms=None, **kwargs):
        """Raises if called, because base class defines method for non-Fact item."""
        raise NotImplementedError

    # ***

    def query_exclude_fact(self, query, fact=None):
        if fact and not fact.unstored:
            query = query.filter(AlchemyFact.pk != fact.pk)
        return query

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
            ValueError: If more than one Fact found at given time.
        """
        query = self.store.session.query(AlchemyFact)

        if fact.start is None:
            raise ValueError("No `start` for starting_at(fact).")

        start_at = query_prepare_datetime(fact.start)
        condition = and_(func.datetime(AlchemyFact.start) == start_at)

        # Excluded 'deleted' Facts.
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712
        query = query.filter(condition)
        # Exclude fact.pk from results.
        query = self.query_exclude_fact(query, fact)
        # Order by (start time, end time, fact ID), ascending.
        query = self.query_order_by_start(query, asc)

        self.store.logger.debug("fact: {} / query: {}".format(fact, str(query)))

        n_facts = query.count()
        if n_facts > 1:
            message = (
                'More than one fact found starting at "{}": {} facts found'.format(
                    fact.start, n_facts
                )
            )
            raise ValueError(message)

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

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
            ValueError: If more than one Fact found at given time.
        """
        query = self.store.session.query(AlchemyFact)

        if fact.end is None:
            raise ValueError("No `end` for ending_at(fact).")

        end_at = query_prepare_datetime(fact.end)
        condition = and_(func.datetime(AlchemyFact.end) == end_at)

        # Excluded 'deleted' Facts.
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712
        query = query.filter(condition)
        # Exclude fact.pk from results.
        query = self.query_exclude_fact(query, fact)
        # Order by (start time, end time, fact ID), descending.
        query = self.query_order_by_start(query, desc)

        self.store.logger.debug("fact: {} / query: {}".format(fact, str(query)))

        n_facts = query.count()
        if n_facts > 1:
            message = 'More than one fact found ending at "{}": {} facts found'.format(
                fact.end,
                n_facts,
            )
            raise ValueError(message)

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

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
        query = self.store.session.query(AlchemyFact)

        if fact is not None:
            if fact.end and isinstance(fact.end, datetime):
                # A Closed Fact.
                ref_time = fact.end
            elif fact.start and isinstance(fact.start, datetime):
                # The Active Fact.
                ref_time = fact.start
        if not isinstance(ref_time, datetime):
            # This branch reachable from factoid_fixture tests. See:
            #   raw_fact: 'Monday-13:00: foo@bar', time_hint: 'verify_both'
            #   raw_fact: '2015-12-12 13:00 foo@bar', time_hint: 'verify_both'
            raise ValueError(_("No reference time for antecedent(fact)."))

        ref_time = query_prepare_datetime(ref_time)

        before_active_fact_start = and_(
            AlchemyFact.end == None,  # noqa: E711
            # Except rather than <=, use less than, otherwise
            # penultimate_fact.antecedent might find the ultimate
            # fact, if that final fact is ongoing.
            #   E.g., considering
            #     fact  1: time-a to time-b
            #     ...
            #     fact -2: time-x to time-y
            #     fact -1: time-y to <now>
            #   antecedent of fact -2 should check time-y < time-y and
            #   not <= otherwise antecedent of fact -2 would be fact -1.
            #   (The subsequent function will see it, though, as it
            #   looks for AlchemyFact.start >= ref_time.)
            func.datetime(AlchemyFact.start) < ref_time,
        )

        # (lb): This intricate query is meant to handle momentaneous Facts. If
        # there were no such Facts, we could check AlchemyFact.end <= ref_time
        # and exclude AlchemyFact.pk == fact.pk, and we'd be fine. But we want
        # to handle momentaneous Facts, so we have 3 ref_time comparisons, not 1.
        # - Note that I originally had an if-else block here: if fact is None,
        #   the code would simply check AlchemyFact.end <= ref_time. The use
        #   case here would be passing a datetime to this method, antecedent,
        #   and not a Fact. For example, if you had a Fact from 11a to 12p,
        #   and a Fact from 12p to 12p, passing a datetime set to 12p would
        #   return whichever of those two Facts has the greater PK (because
        #   of the query_order_by_start later in this method). If that Fact
        #   was the momentaneous Fact, you wouldn't be able to call antecedent
        #   again to get the earlier Fact given the datetime alone -- each time
        #   you pass 12p to this method, you'd get the same Fact. But that's not
        #   how this method would be used -- to handle momentaneous Facts, we
        #   need the Fact object, because we need to compare PKs. So rather
        #   than return a momentaneous Fact when a datetime is passed, skip
        #   them. That is, in the example just given, if given a datetime at
        #   12p, always return the Fact from 11a to 12p. We do this by not
        #   just searching AlchemyFact.end <= ref_time, but instead by using
        #   two search criteria, and checking both AlchemyFact.end < ref_time,
        #   or AlchemyFact.end == ref_time and AlchemyFact.start < ref_time.

        or_criteria = []
        # Get complicated, so we handle momentaneous Facts appropriately.
        # E.g., suppose one Fact's time range is 11a to noon, and another
        # Fact is momentaneous from 12:00:00 to 12:00:00. If user is viewing
        # a third Fact that spans from 12:00:00 to 13:00:00, antecedent
        # should return the momentaneous Fact. If antecedent is called
        # again on the momentaneous Fact, return the one that starts at 11a.
        # Start by including any Fact that ends *before*, but not at, ref_time.
        or_criteria.append(func.datetime(AlchemyFact.end) < ref_time)
        # Next, include any Fact that ends at ref_time but is not momentaneous.
        # Given the previous example of three Facts, given the momentaneous
        # Fact at 12:00:00, this will find the earlier Fact from 11a to 12p.
        or_criteria.append(
            and_(
                func.datetime(AlchemyFact.end) == ref_time,
                func.datetime(AlchemyFact.start) < ref_time,
            )
        )
        # Finally, include any momentaneous Fact that occupies the moment at
        # ref_time, but take into consideration the PK so that calling this
        # method, antecedent, with each momentaneous Fact will return them in
        # a predictable order, and will eventually walk out of the moment.
        if fact is not None and fact.pk is not None:
            # From example, assume there are 2 momentaneous Facts at 12:00:00,
            # this would ensure that, after finding the first one, passing the
            # first one to this method finds the second on, and then passing the
            # second one does not return the first one again. (Note that later
            # we call query_order_by_start to ensure the order is correct.)
            or_criteria.append(
                and_(
                    func.datetime(AlchemyFact.end) == ref_time,
                    func.datetime(AlchemyFact.start) == ref_time,
                    AlchemyFact.pk < fact.pk,
                )
            )
        before_closed_fact_end = and_(
            AlchemyFact.end != None,  # noqa: E711
            or_(*or_criteria),
        )

        condition = or_(
            before_active_fact_start,
            before_closed_fact_end,
        )

        # Excluded 'deleted' Facts.
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712
        query = query.filter(condition)
        # Exclude fact.pk from results.
        query = self.query_exclude_fact(query, fact)
        # Order by (start time, end time, fact ID), descending.
        query = self.query_order_by_start(query, desc)

        query = query.limit(1)

        self.store.logger.debug(
            "fact: {} / ref_time: {} / query: {}".format(fact, ref_time, str(query))
        )

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

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
        query = self.store.session.query(AlchemyFact)

        if fact is not None:
            if fact.start and isinstance(fact.start, datetime):
                ref_time = fact.start
            elif fact.end and isinstance(fact.end, datetime):
                # A Fact whose start None or not Datetime, but has an end.
                # - E.g., start is None or '+10m'; end is Datetime.
                # - See factoid_fixture -- a number of tests branch here.
                #     py.test -x tests/facts/test_add_fact.py
                #     py.test -x -s -k test_add_new_fact tests/
                ref_time = fact.end
        if ref_time is None:
            raise ValueError(_("No reference time for subsequent(fact)."))

        ref_time = query_prepare_datetime(ref_time)

        # See comments in antecedent that explain the logic here (albeit
        # the complementary logic, for searching backwards, not forward).
        or_criteria = []
        or_criteria.append(func.datetime(AlchemyFact.start) > ref_time)
        or_criteria.append(
            and_(
                func.datetime(AlchemyFact.start) == ref_time,
                func.datetime(AlchemyFact.end) > ref_time,
            )
        )
        if fact is not None and fact.pk is not None:
            or_criteria.append(
                and_(
                    func.datetime(AlchemyFact.start) == ref_time,
                    func.datetime(AlchemyFact.end) == ref_time,
                    AlchemyFact.pk > fact.pk,
                )
            )
        # Note that, by design, AlchemyFact.start should always be not None,
        # but we'll check anyway, for completeness and comparability to the
        # antecedent method (where AlchemyFact.end is not always not None).
        condition = and_(
            AlchemyFact.start != None,  # noqa: E711
            or_(*or_criteria),
        )

        # Excluded 'deleted' Facts.
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712
        query = query.filter(condition)
        # Exclude fact.pk from results.
        query = self.query_exclude_fact(query, fact)
        # Order by (start time, end time, fact ID), ascending.
        query = self.query_order_by_start(query, asc)

        query = query.limit(1)

        self.store.logger.debug(
            "fact: {} / ref_time: {} / query: {}".format(fact, ref_time, str(query))
        )

        found = query.one_or_none()
        found_fact = found.as_hamster(self.store) if found else None
        return found_fact

    # ***

    def strictly_during(self, since, until, result_limit=1000):
        """
        Return the fact(s) strictly contained within a since and until time.

        Args:
            since (datetime.datetime):
                Start datetime of facts to find.

            until (datetime.datetime):
                End datetime of facts to find.

            result_limit (int):
                Maximum number of facts to find, else log warning message.

        Returns:
            list: List of ``nark.Facts`` instances.
        """
        query = self.store.session.query(AlchemyFact)

        condition = and_(
            func.datetime(AlchemyFact.start) >= query_prepare_datetime(since),
            or_(
                and_(
                    AlchemyFact.end != None,  # noqa: E711
                    func.datetime(AlchemyFact.end) <= query_prepare_datetime(until),
                ),
                and_(
                    AlchemyFact.end == None,  # noqa: E711
                    func.datetime(AlchemyFact.start) <= query_prepare_datetime(until),
                ),
            ),
        )

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        query = self.query_order_by_start(query, asc)

        self.store.logger.debug(
            "since: {} / until: {} / query: {}".format(since, until, str(query))
        )

        # LATER: (lb): We'll let the client ask for as many records as they
        # want. But we might want to offer ways to deal more gracefully with
        # it, like via pagination; or a fetch_one callback, so that only item
        # gets loaded in memory at a time, rather than everything. For now, we
        # can at least warn, I suppose.
        during_count = query.count()
        if during_count > result_limit:
            # (lb): hamster-lib would `raise OverflowError`,
            # but that seems drastic.
            message = _(
                "This is your alert that lots of Facts were found between "
                "the two dates specified: found {}.".factor(during_count)
            )
            self.store.logger.warning(message)

        facts = query.all()
        found_facts = [fact.as_hamster(self.store) for fact in facts]
        return found_facts

    # ***

    def surrounding(self, fact_time, inclusive=False):
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
            ValueError: If more than one Fact found at given time.
        """
        query = self.store.session.query(AlchemyFact)

        cmp_time = query_prepare_datetime(fact_time)

        if not inclusive:
            condition = and_(
                func.datetime(AlchemyFact.start) < cmp_time,
                # Find surrounding complete facts, or the ongoing fact.
                or_(
                    AlchemyFact.end == None,  # noqa: E711
                    func.datetime(AlchemyFact.end) > cmp_time,
                ),
            )
        else:
            condition = and_(
                func.datetime(AlchemyFact.start) <= cmp_time,
                # Find surrounding complete facts, or the ongoing fact.
                or_(
                    AlchemyFact.end == None,  # noqa: E711
                    func.datetime(AlchemyFact.end) >= cmp_time,
                ),
            )

        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        query = self.query_order_by_start(query, asc)

        self.store.logger.debug(
            "fact_time: {} / query: {}".format(fact_time, str(query))
        )

        if not inclusive:
            n_facts = query.count()
            if n_facts > 1:
                message = 'Broken time frame found at "{}": {} facts found'.format(
                    fact_time, n_facts
                )
                raise ValueError(message)

        facts = query.all()
        found_facts = [fact.as_hamster(self.store) for fact in facts]
        return found_facts

    # ***

    def endless(self):
        """
        Return any facts without a fact.start or fact.end.

        Args:
            <none>

        Returns:
            list: List of ``nark.Facts`` instances.
        """
        query = self.store.session.query(AlchemyFact)

        # NOTE: (lb): Use ==/!=, not `is`/`not`, b/c SQLAlchemy
        #       overrides ==/!=, not `is`/`not`.
        condition = or_(
            AlchemyFact.start == None, AlchemyFact.end == None
        )  # noqa: E711
        condition = and_(condition, AlchemyFact.deleted == False)  # noqa: E712

        query = query.filter(condition)

        self.store.logger.debug("query: {}".format(str(query)))

        facts = query.all()
        found_facts = [fact.as_hamster(self.store) for fact in facts]
        return found_facts

    # ***


# ***
