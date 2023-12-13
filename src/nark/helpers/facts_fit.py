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

""""""

from datetime import datetime

__all__ = (
    'antecedent_fact',
    'subsequent_fact',
)


def antecedent_fact(facts_mgr, new_facts, now_time):
    for fact in new_facts:
        # 2019-01-19: This isn't quite right. We could use earliest
        # clock time if we find first datetime, then look again for
        # clock time....
        if (
            (fact.start and isinstance(fact.start, datetime))
            or (fact.end and isinstance(fact.end, datetime))
        ):
            return facts_mgr.antecedent(fact=fact)
    return facts_mgr.antecedent(ref_time=now_time)


def subsequent_fact(facts_mgr, new_facts):
    for fact in reversed(new_facts):
        if (
            (fact.end and isinstance(fact.end, datetime))
            or (fact.start and isinstance(fact.start, datetime))
        ):
            return facts_mgr.subsequent(fact=fact)
    return None

