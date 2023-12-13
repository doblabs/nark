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

"""This module defines logging related function."""

from gettext import gettext as _

import logging

from ansi_escape_room import attr, fg


def formatter_basic(color=False):
    if not color:
        return formatter_basic_plain()
    return formatter_basic_color()


def formatter_basic_plain():
    formatter = logging.Formatter(
        '[%(levelname)s] '
        '%(asctime)s '
        '%(name)s '
        '%(funcName)s: '
        '%(message)s'
    )
    return formatter


def formatter_basic_color():
    # MAYBE: (lb): Replace hardcoded #styling (styles.conf). (Less concerned about logs.)
    formatter = logging.Formatter(
        '{grey_54}[{underlined}{magenta}%(levelname)s{reset}{grey_54}]{reset} '
        '{yellow}%(asctime)s{reset} '
        '{light_blue}%(name)s '
        '%(funcName)s{reset}: '
        '{bold}{green}%(message)s{reset}'.format(
            # MAGIC: Use RGB not 'grey_54' because tmux 0-255 color issue.
            #   grey_54=fg('grey_54'),
            grey_54=fg('#8a8a8a'),
            underlined=attr('underlined'),
            magenta=fg('magenta'),
            reset=attr('reset'),
            yellow=fg('yellow'),
            light_blue=fg('light_blue'),
            bold=attr('bold'),
            green=fg('green'),
        )
    )
    return formatter


def resolve_log_level(level):
    error = False
    try:
        try:
            log_level = int(level)
        except ValueError:
            log_level = logging.getLevelName(level)
    except KeyError:
        error = True
        log_level = logging.WARNING
    return log_level, error


def set_logger_level(logger_name, logger_log_level):
    logger = logging.getLogger(logger_name)
    logger.addHandler(logging.NullHandler())

    # (lb): BIZARRE: On a 14.04 machine, parent.handlers has StreamHandler
    #   in it, so it prints to console. This does not happen on a 16.04
    #   machine I also use. And I cannot determine the reason (both
    #   machines use a virtualenv configured exactly the same way, and
    #   the Python version is merely off by one PATCH).
    logger.parent.handlers = []
    logger.parent.addHandler(logging.NullHandler())

    log_level, warn_name = resolve_log_level(logger_log_level)

    try:
        logger.setLevel(int(log_level))
    except ValueError:
        warn_name = True
        logger.setLevel(logging.WARNING)

    if warn_name:
        logger.warning(
            _('Unknown log_level specified for ‘{}’: {}')
            .format(logger_name, logger_log_level)
        )

    return logger


def setup_handler(handler, formatter, *loggers):
    handler.setFormatter(formatter)
    for logger in loggers:
        logger.addHandler(handler)

