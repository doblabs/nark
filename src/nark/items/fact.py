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

from ansiwrap_hotoffthehamster import ansilen  # See also: click._compat.term_len


from collections import namedtuple
from collections import Counter
from datetime import datetime
from operator import attrgetter

from ..helpers import fact_time, format_time
from ..helpers.format_text import format_value_truncate
from ..helpers.parsing import parse_factoid
from .activity import Activity
from .category import Category
from .item_base import BaseItem
from .tag import Tag

try:
    from math import inf
except ImportError:  # pragma: no cover: Do not support < 3.5.
    # < Python 3.5.
    inf = float("inf")


__all__ = (
    "SinceTimeBegan",
    "UntilTimeStops",
    "FactTuple",
    "Fact",
)


SinceTimeBegan = datetime(1, 1, 1)


# FIXME/2020-01-27: #Y10Kbug.
UntilTimeStops = datetime(9999, 12, 31, 23, 59, 59)


FactTuple = namedtuple(
    "FactTuple",
    (
        "pk",
        "activity",
        "start",
        "end",
        "description",
        "tags",
        "deleted",
        "split_from",
    ),
)


class Fact(BaseItem):
    """Storage agnostic class for facts."""

    def __init__(
        self,
        activity,
        start,
        end=None,
        pk=None,
        description=None,
        tags=None,
        deleted=False,
        split_from=None,
    ):
        """
        Initiate our new instance.

        Args:
            activity (nark.Activity): Activity associated with this fact.

            start (datetime.datetime): Start datetime of this fact.

            end (datetime.datetime, optional): End datetime of this fact.
                Defaults to ``None``.

            pk (optional): Primary key used by the backend to identify this instance.
                Defaults to ``None``.

            description (str, optional): Additional information relevant to this
                singular fact. Defaults to ``None``.

            tags (Iterable, optional): Iterable of ``strings`` identifying *tags*.
                Defaults to ``None``.

            deleted (bool, optional): True if fact was deleted/edited/split.

            split_from (nark.Fact.id, optional): ID of deleted fact this
                fact succeeds.
        """
        super(Fact, self).__init__(pk, name=None)
        assert activity is None or isinstance(activity, Activity)
        self.activity = activity
        self.start = start
        self.end = end
        self.description = description

        self.tags = []
        self.tags_replace(tags)

        # (lb): Legacy Hamster did not really have an edit-fact feature.
        # Rather, when the user "edited" a Fact, Hamster would delete
        # the existing row and make a new one. This is very unwikilike!
        # To preserve history, let's instead mark edited Facts deleted.
        # FIXME/2018-05-23 10:56: (lb): Add column to record new Facts ID?
        self.deleted = bool(deleted)

        self.split_from = split_from

    def __eq__(self, other):
        if isinstance(other, BaseItem):
            other = other.as_tuple()

        return self.as_tuple() == other

    def equal_sans_end(self, other):
        if isinstance(other, BaseItem):
            other = other.as_tuple(sans_end=True)

        return self.as_tuple(sans_end=True) == other

    def __hash__(self):
        """Naive hashing method."""
        return hash(self.as_tuple())

    def __gt__(self, other):
        return self.sorty_tuple > other.sorty_tuple

    def __lt__(self, other):
        return self.sorty_tuple < other.sorty_tuple

    @property
    def sorty_times(self):
        fact_end = self.end if self.end is not None else UntilTimeStops
        return (self.start, fact_end)

    @property
    def sorty_tuple(self):
        fact_end = self.end if self.end is not None else UntilTimeStops
        fact_pk = self.pk if self.pk is not None else -inf
        return (self.start, fact_end, fact_pk)

    def __str__(self):
        return self.friendly_str()

    def __repr__(self):
        return self.as_kvals()

    def as_kvals(self):
        parts = []
        for key in sorted(self.__dict__.keys()):
            if key == "name":
                # The 'name' attribute is part of BaseItem but not used by Fact.
                # - (lb): Weird: Including this assert causes the coverage to indicate
                #   that the `continue` is not covered. But with the assert commented,
                #   the `continue` is marked correctly as covered. Huh. I even tried
                #   throwing a `pass` after the assert, but same issue. So no assert.
                #     assert self.name is None
                #     pass
                continue
            elif key == "tags":
                val = repr(self.tags_sorted)
            else:
                # Not that nark knows anything about this, but dob's derived
                # class, FactDressed, has a next_fact and prev_fact pointer.
                # To avoid a deadly RecursionError by following pointers of a
                # doubly-linked list, check that the attribute value is not
                # another Fact. (For the sake of coupling, FactDressed could
                # just supply its own __repr__() function, but this function
                # is already doing a lot, so might as well toss in the kitchen
                # sink.)
                raw = getattr(self, key)
                if isinstance(raw, self.__class__):
                    val = id(raw)
                else:
                    val = repr(raw)
            parts.append("{key}={val}".format(key=key, val=val))
        repred = "Fact({})".format(", ".join(parts))
        return repred

    def as_tuple(self, include_pk=True, sans_end=False):
        """
        Provide a tuple representation of this facts relevant attributes.

        Args:
            include_pk (bool): Whether to set the pk to the Fact ID or False.
                Note that if ``False`` ``tuple.pk = False``. This is useful
                for comparing logical Fact equality.

        Returns:
            nark.FactTuple: Representing this categories values.
        """
        pk = self.pk
        if not include_pk:
            pk = False

        activity_tup = self.activity and self.activity.as_tuple(include_pk=include_pk)

        sorted_tags = self.tags_sorted
        ordered_tags = [tag.as_tuple(include_pk=include_pk) for tag in sorted_tags]

        end_time = -1 if sans_end else self.end

        return FactTuple(
            pk=pk,
            activity=activity_tup,
            start=self.start,
            end=end_time,
            description=self.description,
            tags=frozenset(ordered_tags),
            deleted=bool(self.deleted),
            split_from=self.split_from,
        )

    def copy(self, include_pk=True):
        """ """
        new_fact = self.__class__(
            activity=self.activity,
            start=self.start,
            end=self.end,
            description=self.description,
            # self.tags might be an sqlalchemy.orm.collections.InstrumentedList
            # and calling list() on it will create a new list of what could be
            # nark.backends.sqlalchemy.objects.AlchemyTag.
            tags=list(self.tags),
            deleted=bool(self.deleted),
            split_from=self.split_from,
        )
        if include_pk:
            new_fact.pk = self.pk
        return new_fact

    def equal_fields(self, other):
        """
        Compare this instances fields with another fact. This excludes comparing the PK.

        Args:
            other (Fact): Fact to compare this instance with.

        Returns:
            bool: ``True`` if all fields but ``pk`` are equal, ``False`` if not.

        Note:
            This is particularly useful if you want to compare a new ``Fact`` instance
            with a freshly created backend instance. As the latter will probably have a
            primary key assigned now and so ``__eq__`` would fail.
        """
        return self.as_tuple(include_pk=False) == other.as_tuple(include_pk=False)

    # ***

    LOCALIZE = False

    @classmethod
    def localize(cls, localize=None):
        was_localize = cls.LOCALIZE
        if localize is not None:
            cls.LOCALIZE = localize
        return was_localize

    # ***

    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        """
        Make sure that we receive a ``datetime.datetime`` instance,
          or relative time string.

        Args:
            start (datetime.datetime, str): Start datetime of this ``Fact``.

        Raises:
            TypeError: If we receive something other than a ``datetime.datetime``
                (sub-)class or ``None``.
        """
        # MOTE: (lb): The AlchemyFact class derives from this class, but it
        # has columns of the same names as theses @property definitions, e.g.,
        # `start`. So when you set, e.g, `self.start = X` from the AlchemyFact
        # class, it does not call this base class' @setter for start. So don't
        # use self._start except in self.start()/=.
        self._start = fact_time.must_be_datetime_or_relative(start)

    def start_fmt(self, datetime_format="%Y-%m-%d %H:%M:%S"):
        """If start, return a ``strftime``-formatted string, otherwise return ``''``."""
        return self.start.strftime(datetime_format) if self.start else ""

    @property
    def start_fmt_utc(self):
        """FIXME: Document"""
        if not self.start:
            return ""
        # Format like: '%Y-%m-%d %H:%M:%S%z'
        return format_time.isoformat_tzinfo(self.start, sep=" ", timespec="seconds")

    @property
    def start_fmt_local(self):
        """FIXME: Document"""
        if not self.start:
            return ""
        # Format like: '%Y-%m-%d %H:%M:%S'
        return format_time.isoformat_tzless(self.start, sep=" ", timespec="seconds")

    # ***

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end):
        """
        Make sure that we receive a ``datetime.datetime`` instance.

        Args:
            end (datetime.datetime): End datetime of this ``Fact``.

        Raises:
            TypeError: If we receive something other than a ``datetime.datetime``
                (sub-)class or ``None``.
        """
        self._end = fact_time.must_be_datetime_or_relative(end)

    def end_fmt(self, datetime_format="%Y-%m-%d %H:%M:%S"):
        """If end, return a ``strftime``-formatted string, otherwise return ``''``."""
        return self.end.strftime(datetime_format) if self.end else ""

    @property
    def end_fmt_utc(self):
        """FIXME: Document"""
        if not self.end:
            return ""
        return format_time.isoformat_tzinfo(self.end, sep=" ", timespec="seconds")

    @property
    def end_fmt_local(self):
        """FIXME: Document"""
        if not self.end:
            return ""
        return format_time.isoformat_tzless(self.end, sep=" ", timespec="seconds")

    @property
    def end_fmt_local_nowwed(self):
        """FIXME: Document"""
        if not self.end:
            return "{} <now>".format(self.end_fmt_local_or_now)
        return self.end_fmt_local

    @property
    def end_fmt_local_or_now(self):
        if not self.end:
            return "{}".format(
                format_time.isoformat_tzless(
                    self.time_now,
                    sep=" ",
                    timespec="seconds",
                )
            )
        return self.end_fmt_local

    # ***

    @property
    def momentaneous(self):
        if self.times_ok and self.start == self.end:
            return True
        return False

    @property
    def time_now(self):
        return datetime.now() if Fact.localize() else datetime.utcnow()

    @property
    def times(self):
        return (self.start, self.end)

    @property
    def times_ok(self):
        if isinstance(self.start, datetime) and isinstance(self.end, datetime):
            return True
        return False

    # ***

    def delta(self):
        """
        Provide the offset of start to end for this fact.

        Returns:
            datetime.timedelta or None: Difference between start- and end datetime.
                If we only got a start datetime, return ``None``.
        """
        end_time = self.end
        if not end_time:
            end_time = self.time_now

        return end_time - self.start

    def format_delta(self, style="%M", **kwargs):
        """
        Return a string representation of ``Fact().delta``.

        Args:
            formatting (str): Specifies the output format.

              Valid choices are:
                * ``'%M'``: As minutes, rounded down.
                * ``'%H:%M'``: As 'hours:minutes'. rounded down.
                * ``'HHhMMm'``: As '{hours} hour(s) {minutes} minute(s)'.
                * ``''``: As human friendly time.

        Returns:
            str: Formatted string representing this fact's *duration*.
        """
        return format_time.format_delta(self.delta(), style=style, **kwargs)

    # ***

    @property
    def midpoint(self):
        if not self.times_ok:
            return None
        midpoint = self.end - ((self.end - self.start) / 2)
        return midpoint

    @property
    def time_of_day_midpoint(self):
        if not self.midpoint:
            return ""
        clock_sep = " ◐ "
        hamned = "{0}".format(
            self.midpoint.strftime("%a %d %b %Y{0}%I:%M %p").format(clock_sep),
            # FIXME: (lb): Add Colloquial TOD suffix, e.g., "morning".
        )
        return hamned

    def time_of_day_humanize(self, show_now=False):
        if not self.times_ok and not show_now:
            return ""
        clock_sep = " ◐ "
        wkd_day_mon_year = self.start.strftime("%a %d %b %Y")
        text = self.start.strftime("{0}{1}%I:%M %p").format(
            wkd_day_mon_year,
            clock_sep,
        )
        if self.end == self.start:
            return text
        text += _(" — ")
        end_time = self.end if self.end is not None else self.time_now
        text += end_time.strftime("%I:%M %p")
        end_wkd_day_mon_year = end_time.strftime("%a %d %b %Y")
        if end_wkd_day_mon_year == wkd_day_mon_year:
            return text
        text += " "
        text += end_wkd_day_mon_year
        return text

    # ***

    @property
    def activity_name(self):
        """..."""
        try:
            return self.activity.name
        except AttributeError:
            return ""

    # +++

    @property
    def category(self):
        """Just a convenience shim to underlying category object."""
        return self.activity.category

    @property
    def category_name(self):
        """..."""
        try:
            return self.activity.category.name
        except AttributeError:
            return ""

    # +++

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, description):
        """ "
        Normalize all descriptions that evaluate to ``False``.
        Store everything else as string.
        """
        if description:
            description = str(description)
        else:
            description = None
        self._description = description

    @property
    def description_or_empty(self):
        return self.description or ""

    # +++

    def tagnames(self, *args, **kwargs):
        return self.oid_tags(*args, **kwargs)

    def tagnames_sorted_formatted(self, format_tagname):
        return [format_tagname(tag) for tag in self.tags_sorted]

    def tags_replace(self, tags, set_freqs=False):
        new_tags = set()

        # Create a dict-like never-KeyErrors lookup of tag frequency counts.
        tag_freqs = Counter(tags) if set_freqs else None

        for tagn in set(tags) if tags else set():
            if isinstance(tagn, Tag):
                tag = tagn
            else:
                # Retain existing tags rather than replacing with new Tag()s.
                # This is useful for clients that compare changes to a Fact,
                # to avoid a Fact appearing edited when not. For instance, in
                # dob-viewer, after the user uses the Awesome Prompt, even if
                # they just open it and quit it, the returned tags is a list
                # of strs. And dob-viewer sends that string list to the
                # tags_replace method. So be sure to look for existing tag
                # matches and use those -- if we built new Tag()s instead,
                # the new tags would have None for the pk, rather than the
                # ID originally read from the store, and then the fact would
                # false-positive look edited (dirty). And then dob-viewer
                # would bug you to save your unedited Fact, etc.
                tag = next(
                    (tag for tag in self.tags if tag.name == tagn),
                    Tag(
                        name=tagn,
                        freq=tag_freqs[tagn] if set_freqs else 1,
                    ),
                )
            new_tags.add(tag)
        # (lb): Do this in one swoop, and be sure to assign a list; when
        # wrapped by SQLAlchemy, if set to, say, set(), it complains:
        #   TypeError: Incompatible collection type: set is not list-like
        # (Via orm.attribute.CollectionAttributeImpl.set.)
        self.tags = list(new_tags)

    @property
    def tags_sorted(self):
        return sorted(list(self.tags), key=attrgetter("name"))

    # ***

    # ’oid, as in Factoid: these methods help make the friendly, parsable Factoid.

    def oid_stylize(self, oid_part, oid_text):
        """Returns stylized text for a specific part of the Fact*oid*.

        Clients that display Facts where ornamentation matters can override
        this method. This base class implementation is a no-op.
        """
        return oid_text

    def oid_actegory(self, shellify=False, empty_actegory_placeholder=None):
        # (lb): We can skip delimiter after time when using ISO 8601.
        # MAYBE/2020-05-18: I cannot remember, did I want to make '@' char configable?
        if not self.activity_name:
            if not self.category_name:
                if empty_actegory_placeholder is None:
                    act_cat = "@"
                else:
                    act_cat = empty_actegory_placeholder
            else:
                act_cat = "@{}".format(self.category_name)
        else:
            act_cat = "{}@{}".format(
                self.activity_name,
                self.category_name,
            )
        act_cat = self.oid_stylize("act@gory", act_cat)
        act_cat = '"{}"'.format(act_cat) if act_cat and shellify else act_cat
        return act_cat

    def oid_description(self, cut_width=None, sep=", "):
        description = self.description_or_empty
        if description:
            if cut_width is not None and cut_width > 0:
                # Note: whether or not the description length is larger than
                # cut_width, newlines will always be replaced by literal '\n'.
                description = format_value_truncate(description, cut_width)
            description = "{}{}".format(sep, description)
        return description

    # (lb): People associate tags with pound signs -- like, #hashtag!
    # But Bash, and other shells, use octothorpes to start comments.
    # The user can tell Bash to interpret a pound sign as input by
    # "#quoting" it, or by \#delimiting it. Hamster also lets the user
    # use an '@' at symbol instead (not to be confused with typical
    # social media usage of '@' to refer to other users or people).
    # By default, this function assumes the tags do not need special
    # delimiting, and that the pound sign is fine.
    def oid_tags(
        self,
        hashtag_token="#",
        quote_tokens=False,
    ):
        def format_tagname(tag):
            tagged = "{}{}".format(
                self.oid_stylize("#", hashtag_token),
                self.oid_stylize("tag", tag.name),
            )
            tagged = self.oid_stylize("#tag", tagged)
            if quote_tokens:
                tagged = '"{}"'.format(tagged)
            return tagged

        # NOTE: The returned string includes leading space if nonempty!
        tagnames = ""
        if self.tags:
            tagnames = " ".join(self.tagnames_sorted_formatted(format_tagname))
        return tagnames

    # +++

    def friendly_str(
        self,
        shellify=False,
        description_sep=": ",
        tags_sep=": ",
        localize=True,
        include_id=False,
        cut_width_complete=None,
        cut_width_description=None,
        show_elapsed=False,
        empty_actegory_placeholder=None,
    ):
        """
        Flexible Fact serializer.
        """

        def _friendly_str():
            was_localize = Fact.localize(localize)
            meta = assemble_parts()
            result = append_description(meta)
            if cut_width_complete is not None and cut_width_complete > 0:
                result = format_value_truncate(result, cut_width_complete)
            Fact.localize(was_localize)
            return result

        def assemble_parts():
            parts = [
                get_id_string(),
                get_times_string(),
                self.oid_actegory(shellify, empty_actegory_placeholder),
            ]
            parts_str = " ".join(list(filter(None, parts)))
            tags = get_tags_string()
            parts_str += tags_sep + tags if tags else ""
            parts_str += _(" [del]") if self.deleted else ""
            return parts_str

        def append_description(meta):
            # Specify the cut_width if one specified for the complete friendly_str,
            # so that newlines are collapsed into literal '\n' strings, which is a
            # side-effect-feature of using cut_width.
            cut_width = cut_width_description
            if cut_width_complete is not None and cut_width is None:
                cut_width = max(cut_width_complete - ansilen(meta), 0)
            description = self.oid_description(cut_width, description_sep)
            return meta + description

        def get_id_string():
            if not include_id:
                return ""
            # Format the 🏭 🆔 width to be consistent. Assume lifetime of facts?
            # [ [fact]ory ↑ ↑ ID ]
            # - 6 digits: 999,999 facts over 100 years would be ~27 facts per day.
            return self.oid_stylize(
                "pk",
                "(🏭 {})".format(self.pk and "{:6d}".format(self.pk) or "None"),
            )

        def get_times_string():
            times = ""
            times += get_times_string_start()
            times += get_times_string_end(times)
            times += get_times_duration()
            return times

        def get_times_string_start():
            if not self.start:
                return ""
            prefix = ""
            if not self.end:
                prefix = self.oid_stylize("at", "{} ".format(_("at")))
            if not Fact.localize():
                start_time = self.start_fmt_utc
            else:
                start_time = self.start_fmt_local
            start_time = self.oid_stylize("start", start_time)
            return prefix + start_time

        def get_times_string_end(times):
            if not self.end:
                # (lb): Rather than show, e.g., "2020-01-01 01:01 to <now> ...",
                # show a parsable, Factoid-compatible time, "at 2020-01-01 01:01 ...".
                prefix = ""
                end_time = ""
            else:
                # NOTE: The CLI's DATE_TO_DATE_SEPARATORS[0] is 'to'.
                prefix = self.oid_stylize("to", " {} ".format(_("to"))) if times else ""
                if not Fact.localize():
                    end_time = self.end_fmt_utc
                else:
                    end_time = self.end_fmt_local
                end_time = self.oid_stylize("end", end_time)
            return prefix + end_time

        def get_times_duration():
            if not show_elapsed:
                return ""
            duration = " [{}]".format(self.format_delta(style=""))
            return self.oid_stylize("duration", duration)

        def get_tags_string():
            # (lb): There are three ways to "shellify" a hashtag token:
            #         1.) "#quote" it;
            #         2.) \#delimit it; or
            #         3.) use the inoffensive @ symbol instead of #.
            # Let's do 1.) by default, because most people associate the pound
            # sign with tags, because quotes are less offensive than a slash,
            # and because the @ symbol makes me think of "at'ing someone".
            #   Nope:  hashtag_token = '@' if shellify else '#'
            return self.oid_tags(quote_tokens=shellify)

        # ***

        return _friendly_str()

    # +++

    def get_serialized_string(self, shellify=False):
        """
        Return a canonical, "stringified" version of the Fact.

        - Akin to: encoding/flattening/marshalling/packing/pickling.

        This function is mostly meant for machines, not for people.

        - Generally, use ``__str__`` if you want a human-readable string.

          I.e., one whose datetimes are localized relative to the Fact.
          This serializing function defaults to using UTC.

        - Use this function to encode a Fact in a canonical way, which can
          be consumed again later, i.e., using ``Fact.create_from_factoid``.

        - A complete serialized fact might look like this:

              2016-02-01 17:30 to 2016-02-01 18:10 making plans@world domination
              #tag 1 #tag 2, description

          - Note that nark is very unassuming with whitespace. It can be
            used in the Activity and Category names, as well as in tags.

        Attention:

            ``Fact.tags`` is a set and hence unordered. In order to provide
            a deterministic canonical return string, we sort tags by name.
            This is purely cosmetic and does not imply any actual ordering
            of those facts on the instance level.

        Returns:
            str: Canonical string encoding all available fact info.
        """
        return self.friendly_str(shellify=shellify)

    # +++

    @property
    def short(self):
        """
        A brief Fact one-liner.

        (lb): Not actually called by any code, but useful for debugging!
        """
        # HARDCODED: Truncate the string at some length. (This method is for
        # the DEV to use on a PDB prompt, so hardcoding this value if fine.)
        return self.friendly_str(include_id=True, cut_width_complete=59)

    # ***

    @classmethod
    def create_from_factoid(
        cls,
        factoid,
        time_hint="verify_none",
        separators=None,
        lenient=False,
    ):
        """
        Construct a new ``nark.Fact`` from a string of fact details,
            or factoid.

        NOTE: This naïvely creates a new Fact and does not check against
        other Facts for integrity. It's up to the caller to see if the new
        Fact conflicts with existing Facts presently in the system.

        Args:
            factoid (str): Raw fact to be parsed.

            time_hint (str, optional): One of:
                'verify_none': Do not expect to find any time encoded in factoid.
                'verify_both': Expect to find both start and end times.
                'verify_start': Expect to find just one time, which is the start.
                'verify_end': Expect to find just one time, which is the end.
                'verify_then': Time specifies new start; and back-fill interval gap.
                'verify_after': No time spec. Start new Fact at time of previous end.

            lenient (bool, optional): If False, parser raises errors on misssing
                mandatory components (such as time or activity). (Category,
                tags, and description are optional.)

        Returns:
            nark.Fact: New ``Fact`` object constructed from factoid.

        Raises:
            ValueError: If we fail to extract at least ``start`` or ``activity.name``.
            ValueError: If ``end <= start``.
            ParserException: On parser error, one of the many ParserException
                derived classes will be raised.
        """
        parsed_fact, err = parse_factoid(
            factoid,
            time_hint=time_hint,
            separators=separators,
            lenient=lenient,
        )

        new_fact = cls.create_from_parsed_fact(
            parsed_fact,
            lenient=lenient,
        )

        return new_fact, err

    @classmethod
    def create_from_parsed_fact(cls, parsed_fact, lenient=False, **kwargs):
        start = parsed_fact["start"]
        end = parsed_fact["end"]
        # Verify that start > end, if neither are None or not a datetime.
        start, end = fact_time.must_not_start_after_end((start, end))

        activity = ""
        activity_name = parsed_fact["activity"]
        if activity_name:
            activity = Activity(activity_name)
        elif lenient:
            activity = Activity(name="")
        else:
            raise ValueError(_("Unable to extract activity name"))

        category_name = parsed_fact["category"]
        if category_name:
            activity.category = Category(category_name)

        description = parsed_fact["description"]

        tags = parsed_fact["tags"]

        return cls(
            activity, start, end=end, description=description, tags=tags, **kwargs
        )
