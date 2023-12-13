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

import logging
import sys

from gettext import gettext as _

__all__ = (
    'must_verify_log_level',
    'get_log_level_safe',
    'get_log_name_safe',
    # Private:
    #  'LOG_LEVELS',
)


this = sys.modules[__name__]


# ***
# *** Config function: log level helpers.
# ***

# Subset (and lowercase) of logging._nameToLevel.
this.LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


# MEH/2019-01-17: Deal with this when refactoring config:
#   If cli_log_level is wrong, app just logs a warning.
#   But for some reason, here, if sql_log_level is wrong,
#   app dies. Should probably just warning instead and
#   get on with life... print colorful stderr message,
#   but live.
#     See also: nark/nark/control.py and nark/nark/helpers/logging.py
#     have log_level functions, should probably consolidate this!
def must_verify_log_level(level_name):
    if isinstance(level_name, int):
        return level_name
    try:
        log_level = this.LOG_LEVELS[level_name.lower()]
    except AttributeError:
        msg = _(
            " (Unrecognized log level type in config: “{}”. Try a string from: {}.)"
        ).format(level_name, ', '.join(this.LOG_LEVELS))
        raise ValueError(msg)
    except KeyError:
        msg = _(
            " (Unrecognized log level value in config: “{}”. Try one of: ‘{}’.)"
        ).format(level_name, '’, ‘'.join(this.LOG_LEVELS))
        raise ValueError(msg)
    return log_level


def get_log_level_safe(level_name):
    try:
        log_level = must_verify_log_level(level_name)
    except ValueError:
        # MAYBE: (lb): Complain to user that their config value is bad.
        log_level = logging.WARNING

    # (lb): A wee bit of a hack! Don't log during the dob-complete
    #   command, lest yuck!
    # MEH/2020-01-29: If logging to file, don't change level.
    if (len(sys.argv) == 2) and (sys.argv[1] == 'complete'):
        # Disable for dob-complete.
        return logging.CRITICAL + 1
    return log_level


def get_log_name_safe(level):
    return logging.getLevelName(level)

