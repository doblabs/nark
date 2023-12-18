# This file exists within 'nark':
#
#   https://github.com/tallybark/nark
#
# Copyright © 2018-2020 Landon Bouma. All rights reserved.
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

"""Fixtures for testing the SQLAlchemy backend."""

import datetime

import pytest

from nark.tests.backends.sqlalchemy.conftest import *  # noqa: F401, F403


@pytest.fixture(
    params=[
        # 2018-05-05: (lb): I'm so confused. Why is datetime.datetime returned
        # in one test, but freezegun.api.FakeDatetime returned in another?
        # And then for today's date, you use datetime.time! So strange!!
        #
        # I thought it might be because @freezegun.freeze_time only freezes
        # now(), so all other times are not mocked, but note how the frozen
        # 18:00 time, '2015-12-12 18:00', is not mocked in the first two tests,
        # but then it is in the third test!! So confused!
        (
            None,
            None,
            "",
            {
                "since": None,
                "until": None,
            },
        ),
        (
            "2015-12-12 18:00",
            "2015-12-12 19:30",
            "",
            {
                "since": datetime.datetime(2015, 12, 12, 18, 0, 0),
                "until": datetime.datetime(2015, 12, 12, 19, 30, 0),
            },
        ),
        (
            "2015-12-12 18:00",
            "2015-12-12 19:30",
            "",
            {
                "since": datetime.datetime(2015, 12, 12, 18, 0, 0),
                "until": datetime.datetime(2015, 12, 12, 19, 30, 0),
            },
        ),
        (
            "2015-12-12 18:00",
            "",
            "",
            {
                # (lb): Note sure diff btw. FakeDatetime and datetime.
                # 'since': freezegun.api.FakeDatetime(2015, 12, 12, 18, 0, 0),
                "since": datetime.datetime(2015, 12, 12, 18, 0, 0),
                "until": None,  # `not until` becomes None, so '' => None.
            },
        ),
        (
            "2015-12-12",
            "",
            "",
            {
                # 'since': freezegun.api.FakeDatetime(2015, 12, 12, 0, 0, 0),
                "since": datetime.datetime(2015, 12, 12, 0, 0, 0),
                "until": None,  # `not until` becomes None, so '' => None.
            },
        ),
        (
            "13:00",
            "",
            "",
            {
                "since": datetime.datetime(2015, 12, 12, 13, 0, 0),
                "until": None,  # `not until` becomes None, so '' => None.
            },
        ),
    ]
)
def search_parameter_parametrized(request):
    """Provide a parametrized set of arguments for the ``get_all`` command."""
    return request.param
