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

"""Global fixtures."""

import datetime

import fauxfactory
import pytest
from freezegun import freeze_time

from nark.config import decorate_config

# Register the fact_factory, etc.
from nark.tests.item_factories import *  # noqa: F401, F403


# This fixture is used by ``test_helpers`` and ``test_storage``.
@pytest.fixture
def endless_fact(fact_factory):
    """Provide an existing 'ongoing fact'."""
    # (lb): Comment from hamster-lib:
    #   For reasons unknown ``fact.tags`` would be empty
    #   when using the ``fact`` fixture.
    fact = fact_factory()
    fact.end = None
    return fact


def _base_config(tmpdir):
    """Provide a generic baseline configuration."""
    base_config = {
        'db': {
            'orm': 'sqlalchemy',
            'engine': 'sqlite',
            'path': ':memory:',
        },
        'dev': {
            'catch_errors': False,
            'lib_log_level': 'WARNING',
            'sql_log_level': 'WARNING',
        },
        'time': {
            # FIXME: (lb): Make special tests for these less used options
            #        and then just set to default values here, e.g.,
            #           'day_start': '',
            #           'fact_min_delta': 0,
            'day_start': datetime.time(hour=5, minute=30, second=0),
            'fact_min_delta': 60,
        },
    }
    # (lb): The application deals with a ConfigDecorator object, and not a
    # simple dict, which has the advantage that our tests (and any client
    # code) does not need to ensure that it sets all the config values.
    # - However, we still return a dictionary, because we want to be able
    # to change config values without triggering any validation. E.g.,
    # calling config_root['db'].update({'engine': None}) would raise.
    # But we don't want to blow up in the fixture!
    config_root = decorate_config(base_config)
    config = config_root.as_dict()
    return config


@pytest.fixture
def base_config(tmpdir):
    return _base_config(tmpdir)


# 2020-05-27: (lb): tmpdir needed? Not used in _base_config.
# Also, tmpdir is 'function'-scoped, would never work here.
# (But see `py.path.local(tempfile.mkdtemp())` workaround
# used in another session-scoped fixture if you need tmpdir.)
@pytest.fixture(scope="session")
def base_config_ro():
    return _base_config(tmpdir=None)


@pytest.fixture
def start_end_datetimes_from_offset_now():
    """Generate start/end datetime tuple with given offset in minutes."""
    def generate(offset):
        # MAYBE: Use controller.store.now?
        end = datetime.datetime.now().replace(microsecond=0)
        start = end - datetime.timedelta(minutes=offset)
        return (start, end)
    return generate


@pytest.fixture
# (lb): If shouldn't matter if we use now() or utcnow(). Right?
def start_end_datetimes_from_offset_utcnow():
    """Generate start/end datetime tuple with given offset in minutes."""
    def generate(offset):
        # MAYBE: Use controller.store.now?
        end = datetime.datetime.utcnow().replace(microsecond=0)
        start = end - datetime.timedelta(minutes=offset)
        return (start, end)
    return generate


@pytest.fixture(params=(True, False))
def bool_value_parametrized(request):
    """
    Return a parametrized boolean value.

    This is usefull to easily parametrize tests using flags.
    """
    return request.param


# Attribute fixtures (non-parametrized)
@pytest.fixture
def name():
    """Randomized, valid but non-parametrized name string."""
    return fauxfactory.gen_utf8()


@pytest.fixture
def start_end_datetimes(start_end_datetimes_from_offset_now):
    """Return a start/end-datetime-tuple."""
    return start_end_datetimes_from_offset_now(15)


@pytest.fixture
def start_datetime():
    """Provide a datetime at time test is run."""
    # (lb): Note that datetime.datetime is not influenced by freeze_time
    # around whatever test or fixture includes this fixture; only this
    # fixture decorated by freeze_time has an effect.
    return datetime.datetime.utcnow().replace(microsecond=0)


@pytest.fixture(scope="session")
def start_datetime_ro():
    """Provide a datetime at time test is run."""
    # (lb): Note that datetime.datetime is not influenced by freeze_time
    # around whatever test or fixture includes this fixture; only this
    # fixture decorated by freeze_time has an effect.
    return datetime.datetime.utcnow().replace(microsecond=0)


@pytest.fixture
@freeze_time('2015-12-12 2:00')
def start_datetime_early_2am():
    """Provide an arbitrary datetime."""
    # (lb): Because Freezegun, datetime.now() is datetime.utcnow().
    return datetime.datetime.utcnow().replace(microsecond=0)


@pytest.fixture
def description():
    """Return a generic text suitable to mimic a ``Fact.description``."""
    return fauxfactory.gen_iplum()


# New value generation
@pytest.fixture
def new_category_values():
    """Return garanteed modified values for a given category."""
    def modify(category):
        return {
            'name': category.name + 'foobar',
        }
    return modify


@pytest.fixture
def new_tag_values():
    """Return garanteed modified values for a given tag."""
    def modify(tag):
        return {
            'name': tag.name + 'foobar',
        }
    return modify


@pytest.fixture
def new_fact_values(tag_factory, activity_factory):
    """Provide guaranteed different Fact-values for a given Fact-instance."""
    def modify(fact):
        if fact.end:
            end = fact.end - datetime.timedelta(days=10)
        else:
            end = None
        return {
            'activity': activity_factory(),
            'start': fact.start - datetime.timedelta(days=10),
            'end': end,
            'description': fact.description + 'foobar',
            'tags': set([tag_factory() for i in range(5)])
        }
    return modify


# Valid attributes parametrized
@pytest.fixture(params=('', 'cyrillic', 'utf8', ))
def name_string_valid_parametrized(request):
    """Provide a variety of strings that should be valid non-tag *names*."""
    if not request.param:
        return request.param
    return fauxfactory.gen_string(request.param)


@pytest.fixture(params=('cyrillic', 'utf8',))
def name_string_valid_parametrized_tag(request):
    """Provide a variety of strings that should be valid tag *names*."""
    return fauxfactory.gen_string(request.param)


@pytest.fixture(params=(None,))
def name_string_invalid_parametrized(request):
    """Provide a variety of strings that should be valid non-tag *names*."""
    return request.param


@pytest.fixture(params=(None, ''))
def name_string_invalid_parametrized_tag(request):
    """Provide a variety of strings that should be valid tag *names*."""
    return request.param


@pytest.fixture(params=(
    fauxfactory.gen_string('numeric'),
    fauxfactory.gen_string('alphanumeric'),
    fauxfactory.gen_string('utf8'),
    None,
))
def pk_valid_parametrized(request):
    """Provide a variety of valid primary keys.

    Note:
        At our current stage we do *not* make assumptions about the type of primary key.
        Of cause, this may be a different thing on the backend level!
    """
    return request.param


@pytest.fixture(params=(True, False, 0, 1, '', 'foobar'))
def deleted_valid_parametrized(request):
    """Return various valid values for the ``deleted`` argument."""
    return request.param


@pytest.fixture(params='alpha cyrillic latin1 utf8'.split())
def description_valid_parametrized(request):
    """Provide a variety of strings that should be valid *descriptions*."""
    return fauxfactory.gen_string(request.param)


@pytest.fixture(params='alpha cyrillic latin1 utf8'.split())
def tag_list_valid_parametrized(request):
    """Provide a variety of strings that should be valid *descriptions*."""
    return set([fauxfactory.gen_string(request.param) for i in range(4)])

