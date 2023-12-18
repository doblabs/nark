# This file exists within 'nark':
#
#   https://github.com/tallybark/nark
#
# Copyright © 2020 Landon Bouma. All rights reserved.
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

"""Provides string-related functional methods."""

from ansiwrap_hotoffthehamster import shorten

__all__ = ("format_value_truncate",)


# (lb): Note that textwrap/ansiwrap.shorten only truncates on whitespace or hyphens,
# so the actual truncated (shortened) text will not be exactly trunc_width, but will
# instead be *at most* trunc_width.
# - We could alternatively chop exactly at trunc_width, e.g.,
#     val = val[:trunc_width - len(ellipsis)] + ellipsis
#   which would truncate inside words, e.g., "it would trunca...".
#   But this approach only works on ANSI-free text, and we want this function to work
#   with ANSI-encoded (e.g., colorful) output text. So we use the shorten function.
# Note, too, that regardless of trunc_width, this function *always* replaces each
# newline with its escape sequence ("\n"), because it assumes, if it's being called,
# that the caller wants to at least condense the output (fit it all on one line).
def format_value_truncate(val, trunc_width=None):
    if not val:
        return val
    val = "\\n".join(str(val).splitlines())
    if trunc_width is not None and trunc_width > 0:
        # textwrap3 raises ValueError if max shorter than placeholder.
        ellipsis = "..."
        trunc_width = max(trunc_width, len(ellipsis))
        val = shorten(val, trunc_width, placeholder=ellipsis)
    return val
