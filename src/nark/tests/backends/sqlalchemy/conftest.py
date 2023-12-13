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

"""Fixtures to help test the SQLAlchemy backend."""

import copy
import datetime
import os

import fauxfactory
import pytest
from pytest_factoryboy import register
from unittest.mock import patch, PropertyMock

from sqlalchemy import create_engine, event

from nark.backends.sqlalchemy import objects
from nark.backends.sqlalchemy.storage import SQLAlchemyStore
from nark.items.activity import Activity
from nark.items.category import Category
from nark.items.fact import Fact
from nark.items.tag import Tag

from . import common, factories

register(factories.AlchemyCategoryFactory)
register(factories.AlchemyActivityFactory)
register(factories.AlchemyTagFactory)
register(factories.AlchemyFactFactory)


# *** SQLAlchemy fixtures


def implement_transactional_support_fully(engine):
    """
    (lb): A hack to make SQLite SAVEPOINTs work, so that
    session.begin_nested() works, so that if code under
    test calls session.commit(), we can still rollback().
    See the madness explained at:

      http://docs.sqlalchemy.org/en/rel_1_0/dialects/sqlite.html#pysqlite-serializable
    """

    @event.listens_for(engine, "connect")
    def do_connect(dbapi_connection, connection_record):
        # disable pysqlite's emitting of the BEGIN statement entirely.
        # also stops it from emitting COMMIT before any DDL.
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def do_begin(conn):
        # emit our own BEGIN
        conn.execute("BEGIN")


# (lb): Use 'session' scope so that the Session is only configured once
# for all tests. (Note: I also tried `scope='module'`, which seemed to
# work similarly, but 'session' is the intent, so use that scope.)
@pytest.fixture(scope='session')
def alchemy_runner(request):
    """
    Bind an in-memory mock-db to the session object.

    The session object, common.Session, is a global that this module-scoped
    function sets up just once. And then for each test, we'll create a clean
    session to use for testing that we clean up after.

    This is pretty much straight from the factoryboi docs:

      https://factoryboy.readthedocs.io/en/latest/orms.html#sqlalchemy

    """
    engine = create_engine('sqlite:///:memory:')
    implement_transactional_support_fully(engine)
    objects.metadata.bind = engine
    objects.metadata.create_all(engine)
    common.Session.configure(bind=engine)


def _alchemy_session(request):
    """
    Create a new session for each test.

    Reset the database and remove it after each test.

    As suggested by the docs:

        [Using factory_boy with ORMs](
            http://factoryboy.readthedocs.org/en/latest/orms.html#sqlalchemy
        )
    """
    # (lb): 2018-08-22: If we don't create a new Session() for each test,
    # there's one test that triggers a warning, TestFactManager.test_get_all:
    #   /home/user/.virtualenvs/dob/lib/python3.5/site-packages/
    #     sqlalchemy/orm/scoping.py:102: SAWarning: At least one scoped session
    #     is already present.  configure() can not affect sessions that have
    #     already been created.
    # Prepare a new, clean session for each test, lest SQLAlchemy complain.
    session = common.Session()

    # Rather than mock session.commit, use a nested transaction, otherwise
    # items' PK attrs will not be updated.
    # (lb): NOTE: I tried using subtransactions but those didn't work (albeit
    #   that was before I added the implement_transactional_support_fully hack).
    #       session.begin(subtransactions=True)  # (lb): Didn't work for me.
    # This works, but only after having hacked pysqlite to emit BEGIN ourselves.
    session.begin_nested()

    def fin():
        # "Rollback the session => no changes to the database."
        session.rollback()
        # (lb): Call rollback() twice. (For some reason one test,
        # TestFactManager.test_get_all, has five of each item in
        # the db after it runs, and after we can rollback once.
        # Which to me doesn't make sense. But whatever I'm only
        # human, I don't need to understand _everything_.)
        #
        # You can see for yourself with a conditional breakpoint, e.g.,
        #
        #   if session.query('name from categories;').all(): import pdb;pdb.set_trace()
        #
        # (lb): I'm not sure that we need to close, but so far hasn't hurt.
        session.close()
        # "Remove it, so that the next test gets a new Session()."
        common.Session.remove()

    request.addfinalizer(fin)

    return session


@pytest.fixture
def alchemy_session(request):
    return _alchemy_session(request)


@pytest.fixture(scope="session")
def alchemy_session_ro(request):
    return _alchemy_session(request)


@pytest.fixture(params=[
    fauxfactory.gen_utf8(),
    fauxfactory.gen_alphanumeric(),
    ':memory:',
])
def db_path_parametrized(request, tmpdir):
    """Parametrized database paths."""
    if request.param == ':memory:':
        path = request.param
    else:
        path = os.path.join(tmpdir.strpath, request.param)
    return path


def _alchemy_config(request, base_config):
    """Provide a config that is suitable for sqlalchemy stores."""
    config = copy.deepcopy(base_config)
    # MEH/2020-01-07: (lb): This changes nothing; already the base_config default...
    #                       was that the original intent?
    config['db'].update({
        'orm': 'sqlalchemy',
        'engine': 'sqlite',
        'path': ':memory:',
    })
    return config


@pytest.fixture
def alchemy_config(request, base_config):
    """Provide a config that is suitable for sqlalchemy stores."""
    return _alchemy_config(request, base_config)


@pytest.fixture(scope="session")
def alchemy_config_ro(request, base_config_ro):
    return _alchemy_config(request, base_config_ro)


@pytest.fixture(
    params=(
        # SQLite
        {
            'engine': 'sqlite',
            'path': ':memory:',
        },
        # Non-SQLite
        {
            'engine': 'postgres',
            'host': fauxfactory.gen_ipaddr(),
            'port': fauxfactory.gen_integer(),
            'name': fauxfactory.gen_utf8(),
            'user': fauxfactory.gen_utf8(),
            'password': fauxfactory.gen_utf8(),
        },
        {
            'engine': 'postgres',
            'host': fauxfactory.gen_ipaddr(),
            'name': fauxfactory.gen_utf8(),
            'user': fauxfactory.gen_utf8(),
            'password': fauxfactory.gen_utf8(),
        },
    ),
)
def alchemy_config_parametrized(request, alchemy_config):
    """
    Provide a parametrized config that is suitable for sqlalchemy stores.

    We need to build our expectation dynamically if we want to use faked config values.
    """
    config = copy.deepcopy(alchemy_config)
    config['db'].update(request.param)
    if request.param['engine'] == 'sqlite':
        expectation = '{engine}:///{path}'.format(
            engine=request.param['engine'], path=request.param['path'])
    else:
        port = request.param.get('port', '')
        if port:
            port = ':{}'.format(port)
        expectation = '{engine}://{user}:{password}@{host}{port}/{name}'.format(
            engine=request.param['engine'],
            user=request.param['user'],
            password=request.param['password'],
            host=request.param['host'],
            port=port,
            name=request.param['name'],
        )
    return (config, expectation)


@pytest.fixture(params=(
    {'engine': None,
     'path': None},
    # sqlite
    {'engine': 'sqlite',
     'path': None},
    {'engine': 'sqlite',
     'path': ''},
    # Non-sqlite
    {'engine': 'postgres',
     'host': None,
     'name': fauxfactory.gen_utf8(),
     'user': fauxfactory.gen_utf8(),
     'password': fauxfactory.gen_alphanumeric()},
    {'engine': 'postgres',
     'host': fauxfactory.gen_ipaddr(),
     'name': '',
     'user': fauxfactory.gen_utf8(),
     'password': fauxfactory.gen_alphanumeric()},
    {'engine': 'postgres',
     'host': fauxfactory.gen_ipaddr(),
     'name': fauxfactory.gen_utf8(),
     'user': '',
     'password': fauxfactory.gen_alphanumeric()},
    {'engine': 'postgres',
     'host': fauxfactory.gen_ipaddr(),
     'name': fauxfactory.gen_utf8(),
     'user': fauxfactory.gen_utf8(),
     'password': ''}
))
def alchemy_config_missing_store_config_parametrized(request, alchemy_config):
    """
    Provide an alchemy config containing invalid key/value pairs for
    store initialization.
    """
    config = copy.deepcopy(alchemy_config)
    config['db'].update(request.param)
    return config


def _alchemy_store(request, alchemy_config, alchemy_runner, alchemy_session):
    """
    Provide a SQLAlchemyStore that uses our test-session.

    Note:
        The engine created as part of the store.__init__() goes simply unused.
    """
    # (lb): There was a note from hamster-lib:
    #   "probably want this to autouse=True"
    # but after reviewing the docs, I'm guessing there's no point, because an
    # autouse fixture does not return a value, and the code we'd be replacing
    # -- alchemy_session -- creates the common.Session() object that each test
    # uses. So if we removed alchemy_session from the parameters for each test,
    # each test would still have to find the session object somehow.
    #   https://docs.pytest.org/en/latest/fixture.html#autouse-fixtures-xunit-setup-on-steroids
    store = SQLAlchemyStore(alchemy_config)
    with patch(
        'sqlalchemy_migrate_hotoffthehamster.versioning.api.version',
        new_callable=PropertyMock,
    ) as mock_version:
        # return_value does not matter so long as it's an int.
        type(mock_version).value = PropertyMock(return_value=3)
        store.standup(alchemy_session)
    return store


@pytest.fixture
@patch('nark.backends.sqlalchemy.storage.create_engine',
       lambda *args, **kwargs: None)
@patch('nark.backends.sqlalchemy.objects.metadata.create_all',
       lambda *args, **kwargs: None)
@patch('sqlalchemy_migrate_hotoffthehamster.versioning.api.db_version',
       lambda *args, **kwargs: None)
@patch('sqlalchemy_migrate_hotoffthehamster.versioning.api.downgrade',
       lambda *args, **kwargs: None)
@patch('sqlalchemy_migrate_hotoffthehamster.versioning.api.upgrade',
       lambda *args, **kwargs: None)
@patch('sqlalchemy_migrate_hotoffthehamster.versioning.api.version_control',
       lambda *args, **kwargs: None)
# (lb): 'sqlalchemy_migrate_hotoffthehamster.versioning.api.version'
#       is more complicated; see with-patch, below.
def alchemy_store(request, alchemy_config, alchemy_runner, alchemy_session):
    return _alchemy_store(request, alchemy_config, alchemy_runner, alchemy_session)


@pytest.fixture(scope="session")
def alchemy_store_ro(request, alchemy_config_ro, alchemy_runner, alchemy_session_ro):
    return _alchemy_store(request, alchemy_config_ro, alchemy_runner, alchemy_session_ro)


# ***

@pytest.fixture
def alchemy_activity_deleted(alchemy_activity_factory):
    alchemy_activity = alchemy_activity_factory()
    alchemy_activity.deleted = True
    return alchemy_activity


# Instance sets
# Convenience fixtures that provide multitudes of certain alchemy instances.
@pytest.fixture
def set_of_categories(alchemy_category_factory):
    """Provide a number of perstent facts at once."""
    return [alchemy_category_factory() for i in range(5)]


@pytest.fixture
def set_of_tags(alchemy_tag_factory):
    """Provide a number of perstent facts at once."""
    return [alchemy_tag_factory() for i in range(5)]


def _set_of_alchemy_facts(
    start_datetime,
    alchemy_fact_factory,
    num_facts=5,
    endless=False,
    contiguous=False,
):
    """
    Provide a multitude of generic persistent facts.

    Facts have one day offset from each other and last 20 minutes each.
    """
    start = start_datetime
    result = []

    for i in range(num_facts):
        if i < num_facts - 1:
            end = start + datetime.timedelta(minutes=20)
        else:
            end = None
        fact = alchemy_fact_factory(start=start, end=end)
        result.append(fact)
        if not contiguous:
            start = start + datetime.timedelta(days=1)
        else:
            start = end
    return result


@pytest.fixture
def set_of_alchemy_facts(start_datetime, alchemy_fact_factory):
    return _set_of_alchemy_facts(start_datetime, alchemy_fact_factory, endless=False)


@pytest.fixture
def set_of_alchemy_facts_active(start_datetime, alchemy_fact_factory):
    return _set_of_alchemy_facts(start_datetime, alchemy_fact_factory, endless=True)


@pytest.fixture
def set_of_alchemy_facts_contiguous(start_datetime_early_2am, alchemy_fact_factory):
    # Freeze time early via start_datetime_early_2am so five facts are on the same day.
    return _set_of_alchemy_facts(
        start_datetime_early_2am, alchemy_fact_factory, endless=False, contiguous=True,
    )


@pytest.fixture(scope="session")
def set_of_alchemy_facts_ro(start_datetime_ro):
    # (lb): This confuses me. If pytest-factoryboy `register()` is inherently
    # 'function'-scoped, how does accessing the factory directly seem to work
    # just fine?
    alchemy_fact_factory_ro = factories.AlchemyFactFactory
    return _set_of_alchemy_facts(
        start_datetime_ro, alchemy_fact_factory_ro, endless=False,
    )


# ***

# Fallback nark object and factory fixtures. Unless we know how factories
# interact.
@pytest.fixture
def category_factory(request, name):
    """Provide a ``nark.Category`` factory."""
    def generate():
        return Category(name, None)
    return generate


@pytest.fixture
def category(request, category_factory):
    """Provide a randomized ``nark.Category`` instance."""
    return category_factory()


@pytest.fixture
def tag_factory(request, name):
    """Provide a ``nark.Tag`` factory."""
    def generate():
        return Tag(name, None)
    return generate


@pytest.fixture
def tag(request, tag_factory):
    """Provide a randomized ``nark.Tag`` instance."""
    return tag_factory()


@pytest.fixture
def activity_factory(request, name, category_factory):
    """
    Provide a ``nark.Activity`` factory.

    Note:
        * The returned activity will have a *new* category associated as well.
        * Values are randomized but *not parametrized*.
    """
    def generate():
        category = category_factory()
        return Activity(name, pk=None, category=category, deleted=False)
    return generate


@pytest.fixture
def activity(request, activity_factory):
    """Provide a randomized ``nark.Activity`` instance."""
    return activity_factory()


@pytest.fixture
def fact_factory(
    request, activity_factory, tag_factory, start_end_datetimes, description,
):
    """
    Provide a ``nark.Fact`` factory.

    Note:
        * The returned fact will have a *new* activity (and by consequence category)
          associated as well.
        * Values are randomized but *not parametrized*.
    """
    def generate():
        activity = activity_factory()
        tags = set([tag_factory() for i in range(1)])
        start, end = start_end_datetimes
        fact = Fact(activity, start, end, pk=None, description=description, tags=tags)
        return fact
    return generate


@pytest.fixture
def fact(request, fact_factory):
    """Return a randomized ``nark.Fact`` instance."""
    return fact_factory()

