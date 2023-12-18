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

"""This module provides nark raw fact parsing-related functions."""

import re
from datetime import timedelta
from gettext import gettext as _
from string import punctuation

import lazy_import

from .fact_time import (
    RE_PATTERN_RELATIVE_CLOCK,
    RE_PATTERN_RELATIVE_DELTA,
    datetime_from_clock_prior,
    parse_clock_time,
)
from .parse_errors import ParserInvalidDatetimeException

# Profiling: `import dateparser` takes ~ 0.2 seconds.
dateparser = lazy_import.lazy_module("dateparser")

# Profiling: load iso8601: ~ 0.004 secs.
iso8601 = lazy_import.lazy_module("iso8601")

__all__ = (
    "HamsterTimeSpec",
    "parse_dated",
    "parse_datetime_iso8601",
    "parse_relative_minutes",
)


# =================
# Notes on ISO 8601
# =================
#
# ASIDE: (lb): It's not my intent to write a datetime parser (there are plenty
# out there!), but our flexible factoid format lets the user specify datetimes
# in different, non-standard ways. E.g., the user can use relative time, which
# needs business logic to transform into a real datetime. So it's up to us to
# at least parse the datetime well enough to identify what type of format it's
# in, and then to either process it ourselves, or filter it through ``iso8601``
# or ``dateparser``.
#
# Some examples of ISO 8601 compliant datetimes
# ---------------------------------------------
#
#     ✓ 2018-05-14
#     ✓ 2018-05-14T22:29:24.123456+00:00
#     ✓ 2018-05-14T22:29:24+00:00
#     ✓ 2018-05-14T22:29:24Z
#     ✓ 20180514T222924Z
#
# Not all formats are supported by the ``iso8601`` parser
# -------------------------------------------------------
#
#     ✗ 2018-W20
#     ✗ 2018-W20-1
#     ✗ --05-14
#     ✗ 2018-134
#     ✓ 2018-12
#     ✗ 201805
#     ✓ 2018
#   __ ______________________________________________
#     ^ indicates if parse-worthy by iso8601 (✓ or ✗).
#
# And the ``iso8601`` parser also supports an extended format
# -----------------------------------------------------------
#
#   - The iso8601 parser allows ' ' in lieu of 'T'.
#
# The iso8601 parser format is: ``Date [Time [Timezone]]``
# --------------------------------------------------------
#
#   - Date and time are separated by ' ' or 'T'.
#
#   - Timezone immediately follow Time (no delimiter/space).
#
#   - Dates: YYYY-MM-DD | YYYYMMDD | YYYY-MM | YYYY
#
#   - Times: hh:mm:ss.nn | hhmmss.nn | hh:mm | hhmm | hh
#
#   - Time zones: <nothing> | Z | +/-hh:mm | +/-hhmm | +/-hh
#
#   - You can specify days or months without leading 0s [(lb): but why?].


class HamsterTimeSpec(object):
    """"""

    RE_HAMSTER_TIME = None

    def __init__(self):
        """Not implemented: Use class as static/global, not instantiated."""
        raise NotImplementedError

    @staticmethod
    def discern(hamster_time):
        """
        Check for magic datetimes:
          - '+/-n' relative;
          - 'nn:nn' clocktime;
          - ISO 8601 datetime.

        NOTE: This fcn. does not make datetime.datetime's; that's up to the caller.
        """
        dt, type_dt, sep, rest = None, None, None, None

        if HamsterTimeSpec.RE_HAMSTER_TIME is None:
            HamsterTimeSpec.setup_re()

        match = HamsterTimeSpec.RE_HAMSTER_TIME.match(hamster_time)
        if match is not None:
            say_what = match.groupdict()
            if say_what["relative"]:
                assert dt is None
                dt = say_what["relative"]
                type_dt = "relative"
            if say_what["clock_time"]:
                assert dt is None
                dt = say_what["clock_time"]
                type_dt = "clock_time"
            if say_what["datetime"]:
                assert dt is None
                dt = say_what["datetime"]
                type_dt = "datetime"
            assert dt is not None
            sep = say_what["sep"]
            rest = say_what["rest"]

        return dt, type_dt, sep, rest

    @staticmethod
    def setup_re():
        # NOTE: This pattern isn't perfect; and that's why we use the
        #       iso8601.parse_date routine.
        #
        #       (lb): It's because we use the ()? optionals.
        #       If one of the optionals is formatted incorrectly,
        #       the pattern here happily ignores it, because ?
        #       For instance, this matches, but the microseconds has an error:
        #
        #           RE_HAMSTER_TIME.match('2018-05-14 22:29:24.123x456+00:02')

        # Perhaps a lesser known feature: Hamster allows relative time!!
        pattern_relative = "(?P<relative>([-+]?(\d+h)|[-+](\d+h)?\d+m?))"

        # Reminder: (?:...) is a non-capturing group.

        # Note: This regex does not verify hours and minutes in range 0..59.
        # - Whatever matches this, we'll re-parse with parse_clock_time, which
        #   does a more thorough match.
        pattern_just_clock = (
            "(?P<clock_time>"
            "(?:(\d{1,2}:\d{2}:\d{2}|\d{1,2}:?\d{2}))"
            "(?:(a|am|A|AM|p|pm|P|PM)?)"
            ")"
        )

        # (lb): Treat 4 digits as clock time, not year, i.e.,
        #   `2030` should be 10:30 PM, not Jan 01, 2030.
        # This steals colon-less clock times:
        #   '(?:(\d{8}|\d{4}|\d{4}-\d{1,2}(-\d{1,2})?))'
        pattern_date = "(?:(\d{8}|\d{4}-\d{1,2}(-\d{1,2})?))"
        # BEWARE: Does not verify hours and minutes in range 0..59.
        pattern_time = (
            # (lb): We could allow 3-digit times... but, no.
            #   '(?:\d{1,2})'
            "(?:\d{2})"
            "(?::?\d{2}"
            "(?::?\d{2}"  # noqa: E131
            "(?:\.\d+)?"  # noqa: E131
            ")?"
            ")?"
        )
        pattern_zone = (
            "(?:("
            "Z"  # noqa: E131
            "|"
            "[+-]\d{2}(:?\d{2})?"
            "))?"
        )
        pattern_datetime = "(?P<datetime>{}([ T]{}{})?)".format(
            pattern_date, pattern_time, pattern_zone
        )

        hamster_pattern = "(^|\s)({}|{}|{})(?P<sep>[,:]?)(?=\s|$)(?P<rest>.*)".format(
            pattern_relative,
            pattern_just_clock,
            pattern_datetime,
        )

        # Use re.DOTALL to match newlines, which might be part
        # of the <rest> of the factoid.
        HamsterTimeSpec.RE_HAMSTER_TIME = re.compile(hamster_pattern, re.DOTALL)

    @staticmethod
    def has_time_of_day(raw_dt):
        # Assuming format is year-mo-day separated from time of day by space or 'T'.
        parts = re.split(r" |T", raw_dt)
        if len(parts) != 2:
            return False
        # BEWARE: RE_PATTERN_RELATIVE_CLOCK does not validate range, e.g., 0..59.
        # - But this is just an assert, so should not fire anyway.
        assert re.match(RE_PATTERN_RELATIVE_CLOCK, parts[1]) is not None
        return True


# ***


def parse_dated(dated, time_now, cruftless=False):
    """"""

    def _parse_dated():
        if not isinstance(dated, str):
            # Let BaseFactManager.get_all() process, if not already datetime.
            return dated
        dt, type_dt, sep, rest = HamsterTimeSpec.discern(dated)
        if cruftless and rest:
            msg = _("Found more than datetime in")
            plus_sep = sep and " + ‘{}’".format(sep) or ""
            raise ParserInvalidDatetimeException(
                "{} “{}”: ‘{}’{} + ‘{}’".format(msg, dated, str(dt), plus_sep, rest)
            )
        parsed_dt = None
        if dt is not None:
            parsed_dt = datetime_from_discerned(dated, dt, type_dt)
        if parsed_dt is None:
            # FIXME/2020-05-09: Time zone awareness. Use local_tz.
            parsed_dt = parse_datetime_human(dated, time_now, local_tz=None)
        if parsed_dt is None:
            raise ParserInvalidDatetimeException(
                "{}: “{}”".format(_("Unparseable datetime"), dated)
            )
        return parsed_dt

    def datetime_from_discerned(dated, dt, type_dt):
        if type_dt == "datetime":
            # FIXME: (lb): Implement timezone/local_tz.
            dt_suss = parse_datetime_iso8601(dt, must=True, local_tz=None)
        # else, relative time, or clock time; let caller handle.
        elif type_dt == "clock_time":
            # Note that HamsterTimeSpec.discern is a little lazy and does
            # not verify the clock time is valid values, e.g., hours and
            # minutes between 0..59. But parse_clock_time cares.
            clock_time = parse_clock_time(dt)
            if not clock_time:
                return None

            # FIXME/2020-05-09 13:08: Use day_start here? (Or otherwise address issue
            # where clock time near now gets set nearly 24 hours later, not what user
            # meant.
            #            day_start = self.config['time.day_start']

            dt_suss = datetime_from_clock_prior(time_now, clock_time)
        else:
            assert type_dt == "relative"
            rel_mins, negative = parse_relative_minutes(dt)
            dt_suss = time_now + timedelta(minutes=rel_mins)
        return dt_suss

    return _parse_dated()


# ***

# The powerful dateparser parser can be a little too inclusive.
# - For instance, it'll accept `18 55`, parsed as the 18th day of today's month
#   in the year 2055; or even `44`, read as last century's 44th year, e.g., 1944.
# - The previous two examples, `18 55` and `44`, can be avoided by setting
#   STRICT_PARSING to True.
# - But strict parsing excludes such friendly single-day or single-month
#   inputs, e.g., `Monday` and `January`.
# - But strict parsing also allows input we'd like to ignore, e.g., even if
#   strict, `18:555` parses to Datetime(2055, 1, 8, 5, 0). What a stretch!
# - Note that a parser higher up in nark will have gone the quick route and
#   parsed the value already as a datetime if it was all numbers and maybe
#   some punctuation, e.g., something of the format `YYYY-MM-DD` or `HH:MM`
#   or similar. It's not relying on the dateparser for these simple queries.
# - So do an upfront check and skip the friendly parser if the input is
#   only numbers, whitespace, and/or punctuation, but no alpha characters.

RE_ONLY_09_WH_AND_PUNCT = re.compile(r"^[0-9\s{}]+$".format(re.escape(punctuation)))


def parse_datetime_get_settings(time_now=None, local_tz=None):
    # For settings def, see:
    #
    #   https://github.com/scrapinghub/dateparser/blob/master/docs/usage.rst#settings
    #
    #   dateparser/dateparser_data/settings.py
    #
    # Settings help:
    #
    # - PREFER_DATES_FROM:         defaults to current_period.
    #                              Options are future or past.
    # - SUPPORT_BEFORE_COMMON_ERA: defaults to False.
    # - PREFER_DAY_OF_MONTH:       defaults to current.
    #                              Could be first and last day of month.
    # - SKIP_TOKENS:               defaults to [‘t’]. Can be any string.
    # - TIMEZONE:                  defaults to UTC. Can be timezone abbrev
    #                              or any of tz database name as given here:
    #       https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
    # - RETURN_AS_TIMEZONE_AWARE:  return tz aware datetime objects in
    #                              case timezone is detected in the date string.
    # - RELATIVE_BASE:             count relative date from this base date.
    #                              Should be datetime object.
    #
    # Settings defaults:
    #
    #   'PREFER_DATES_FROM': 'current_period',  # Or: 'past', 'future'.
    #   'PREFER_DAY_OF_MONTH': 'current',  # Or: 'first', 'last'.
    #   'SKIP_TOKENS': ["t"],
    #   'SKIP_TOKENS_PARSER': ["t", "year", "hour", "minute"],
    #   'TIMEZONE': 'local',
    #   'TO_TIMEZONE': False,
    #   'RETURN_AS_TIMEZONE_AWARE': 'default',
    #   'NORMALIZE': True,
    #   'RELATIVE_BASE': False,
    #   'DATE_ORDER': 'MDY',
    #   'PREFER_LOCALE_DATE_ORDER': True,
    #   'FUZZY': False,
    #   'STRICT_PARSING': False,
    #   'RETURN_TIME_AS_PERIOD': False,
    #   'PARSERS': default_parsers,
    #
    settings = {
        # Default to no time zone. We'll set True next, if local_tz.
        "RETURN_AS_TIMEZONE_AWARE": False,
        # So that, e.g., `dob list --since January` uses January 1st, and
        # not January whatever-today's-day-of-the-month-is, set DOM pref.
        "PREFER_DAY_OF_MONTH": "first",
        # Note that when STRICT_PARSING is False, it allows, e.g., `18 55`
        # to mean Datetime(2055, 12, 18, 0, 0), given a
        # today of Datetime(2015, 12, 10, 12, 30). But we
        # use RE_ONLY_09_WH_AND_PUNCT to avoid that.
        "STRICT_PARSING": False,
        # 2020-06-21: (lb): Code does not currently know time zone, and dateparser
        # says 'TIMEZONE' defaults to 'UTC', but I find I have to still specify
        # this value here, otherwise, when testing locally (but does not affect
        # Travic CI, apparently), the get_date_data() return is being adjusted
        # for my timezone. E.g., with a @freeze_time('2015-12-25 18:00'), calling
        # get_date_data('yesterday') returns '2015-12-24 12:00', which is 1 day
        # ago, but adjusted another 6 hours for 'America/Chicago'. IDGI, but
        # apparently being explicit here fixes the issue.
        "TIMEZONE": "UTC",
        # FEAT_REQ/2021-02-07: Should probably make date format configurable:
        # 'DATE_ORDER': 'MDY'|'DMY'|'YMD'|'YDM'
    }

    if time_now:
        # Using RELATIVE_BASE allows friendlies relative to other time, e.g.,
        # '1 hour ago', as in `dob from 1 hour ago to 2018-05-22 20:47` or
        # `dob list --since '1 hour ago'`, etc.
        settings["RELATIVE_BASE"] = time_now

    if local_tz:
        # NOTE: Uses machine-local tz, unless TIMEZONE set.
        settings["RETURN_AS_TIMEZONE_AWARE"] = True
        settings["TIMEZONE"] = local_tz

    return settings


def parse_datetime_human(datepart, time_now=None, local_tz=None):
    # Bouncer (aka Guard Clause): Callers have done their due diligence to
    # handler input that's numbers and punctuation only, so return early if
    # so.
    if RE_ONLY_09_WH_AND_PUNCT.match(datepart) is not None:
        return

    settings = parse_datetime_get_settings(time_now, local_tz)

    # Use the parse() wrapper class, so that the detected language is reused every
    # time, potentially speeding up a long import job. So avoid calling just this:
    #   parsed = dateparser.parse(datepart, settings=settings)
    ddp = dateparser.DateDataParser(settings=settings).get_date_data(datepart)
    # ddp is dict: 'date_obj' is None or the datetime;
    #              'period' is None or, e.g., 'day';
    #              'locale' is None or, e.g., 'en'.
    parsed = ddp["date_obj"]

    return parsed


# DateDataParser Notes
# ====================
#
# 2021-02-07: Note that dateparser uses non-numeric text as a language hint.
#
# Normally we don't care too much, because we're trying to be generous and
# let the user express themselves as loosely as possible. But the presence
# of text has some nuance that might be of interest, especially if you're
# trying to troubleshoot a peculiar parse result. (Which is why I ended
# up documenting this; normally the dob-import file-level parse_input.py
# parser strips a 'to' prefix, as in 'to YYYY-MM-DD', but it had been
# letting 'to' slip through if the line started with punctuation, e.g.,
# '[to YYYY-MM-DD...]', which led me to make the following observations.)
#
# For an example of how dateparser reacts to text, consider this setup:
#
#   (Pdb) ddp = dateparser.DateDataParser(settings=settings)
#
# Then, for example, a datetime string without text defaults to English:
#
#                          v (no prefix)
#   (Pdb) ddp.get_date_data('2021-02-05 22:04')
#   {'date_obj': datetime.datetime(2021, 2, 5, 22, 4), 'locale': 'en', ...}
#                                       ^^^^^ February 5   English^^
#
# But adding a seemingly innocuous 'o' prefix causes it to be interpreted
# as Polish, which defaults to Y-D-M, not Y-M-D, e.g.,
#
#                            v ('o')
#   (Pdb) ddp.get_date_data('o 2021-02-05 22:04')
#   {'date_obj': datetime.datetime(2021, 5, 2, 22, 4), 'locale': 'pl', ...}
#                                       ^^^^^ May 2        Polish ^^
#
# Going one character further, change 'o' to 'to' and it's considereds Finnish:
#
#                            vv ('to')
#   (Pdb) ddp.get_date_data('to 2021-02-05 22:04')
#   {'date_obj': datetime.datetime(2021, 5, 2, 22, 4), 'locale': 'fi', ...}
#                                       ^^^^^ May 2       Finnish ^^
#
# And then if the prefix is not a recognized article of speech from a supported
# language, it won't match at all, e.g.,
#
#   (Pdb) ddp.get_date_data('lo 2021-02-05 22:04')
#   {'date_obj': None, 'period': 'day', 'locale': None}
#
# Knowing that, we can probably guess the result if we indicate "the" date,
# mais *en français*:
#
#   (Pdb) ddp.get_date_data('le 2021-02-05 22:04')
#   {'date_obj': datetime.datetime(2021, 5, 2, 22, 4), 'locale': 'fr', ...}
#
# And finally here's what it looks like for English, using "the", and also
# including punctuation to show that DateDataParser ignores it:
#
#   (Pdb) ddp.get_date_data('*$%![the 2021-02-05 22:04')
#   {'date_obj': datetime.datetime(2021, 2, 5, 22, 4), 'locale': 'en', ...}


# ***


def parse_datetime_iso8601(datepart, must=False, local_tz=None):
    try:
        # NOTE: Defaults to datetime.timezone.utc.
        #       Uses naive if we set default_timezone=None.
        parsed = iso8601.parse_date(datepart, default_timezone=local_tz)
    except iso8601.iso8601.ParseError as err:
        parsed = None
        if must:
            raise ParserInvalidDatetimeException(
                _(
                    "Unable to parse iso8601 datetime: {} [{}]".format(
                        datepart, str(err)
                    )
                )
            )
    return parsed


# ***


def parse_relative_minutes(rel_time):
    rel_mins = None
    negative = None
    # NOTE: re.match checks for a match only at the beginning of the string.
    match = RE_PATTERN_RELATIVE_DELTA.match(rel_time)
    if match:
        parts = match.groupdict()
        rel_mins = 0
        if parts["minutes"]:
            rel_mins += int(parts["minutes"])
        if parts["hours"]:
            rel_mins += int(parts["hours"]) * 60
        if parts["signage"] == "-":
            negative = True  # Because there's no such thang as "-0".
            rel_mins *= -1
        else:
            negative = False
    return rel_mins, negative
