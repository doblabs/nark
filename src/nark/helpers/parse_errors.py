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

__all__ = (
    'ParserException',
    'ParserMissingDatetimeException',
    'ParserMissingDatetimeOneException',
    'ParserMissingDatetimeTwoException',
    'ParserInvalidDatetimeException',
    'ParserMissingSeparatorActivity',
    'ParserMissingActivityException',
)


class ParserException(Exception):
    """Raised if parser cannot decipher nark factoid string."""
    pass


class ParserMissingDatetimeException(ParserException):  # noqa: E302
    """Raised if the raw_fact is missing one or both datetime tokens."""
    pass


class ParserMissingDatetimeOneException(ParserMissingDatetimeException):  # noqa: E302
    """Raised if the raw_fact is missing its start datetime token(s)."""
    pass


class ParserMissingDatetimeTwoException(ParserMissingDatetimeException):  # noqa: E302
    """Raised if the raw_fact is missing its end datetime token(s)."""
    pass


class ParserInvalidDatetimeException(ParserException):  # noqa: E302
    """Raised if a time from raw_fact in not parseworthy."""
    pass


class ParserMissingSeparatorActivity(ParserException):  # noqa: E302
    """Raised if activity@category separator not found."""
    pass


class ParserMissingActivityException(ParserException):  # noqa: E302
    """Raised if factoid is missing: act@cat, cat@, @cat, or just @."""
    pass

