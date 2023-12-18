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

"""Fixtures that are of general use."""

import pytest
from configobj import ConfigObj

from nark.config.log_levels import LOG_LEVELS


@pytest.fixture(
    params=list(LOG_LEVELS.keys())
    + [
        123,
    ]
)
def log_level_valid_parametrized(request):
    """Return each of the valid log level strings."""
    return request.param


@pytest.fixture(params=(None, "123", "abc", ""))
def log_level_invalid_parametrized(request):
    """Return selection of invalid log level strings."""
    return request.param


@pytest.fixture
def configobj_instance(request):
    """Provide a ``ConfigObj`` instance and its expected config dict."""

    config = ConfigObj()
    config["db"] = {}
    config["db"]["orm"] = "sqlalchemy"
    config["db"]["engine"] = "sqlite"
    config["db"]["path"] = "/tmp/nark-tests-config.db"
    config["db"]["host"] = "www.example.com"
    config["db"]["port"] = 22
    config["db"]["name"] = "hamster"
    config["db"]["user"] = "hamster"
    config["db"]["password"] = "hamster"
    config["dev"] = {}
    config["dev"]["catch_errors"] = False
    config["dev"]["lib_log_level"] = "WARNING"
    config["dev"]["sql_log_level"] = "debug"
    config["time"] = {}
    config["time"]["allow_momentaneous"] = False
    config["time"]["day_start"] = "05:00:00"
    config["time"]["fact_min_delta"] = 60

    expectation = {
        "db": {
            "orm": "sqlalchemy",
            "engine": "sqlite",
            "path": "/tmp/nark-tests-config.db",
            "host": "www.example.com",
            "port": "22",
            "name": "hamster",
            "user": "hamster",
            "password": "hamster",
        },
        "dev": {
            # Devmode catch_errors could be deadly under test, as it sets a trace trap.
            "catch_errors": "False",
            "lib_log_level": "WARNING",
            "sql_log_level": "debug",
        },
        "time": {
            # allow_momentaneous is hidden, so won't show in as_dict, etc.
            #  'allow_momentaneous': 'False',
            "day_start": "05:00:00",
            "fact_min_delta": "60",
            # MAYBE: (lb): Consider fiddling with day_start and fact_min_delta
            # in specific tests and leaving them set to factory defaults here:
            #   'day_start': '',
            #   'fact_min_delta': 0,
        },
    }

    return config, expectation
