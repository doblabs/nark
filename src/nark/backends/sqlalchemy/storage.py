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

"""``nark`` object store."""

from gettext import gettext as _

import os.path

# Profiling: load create_engine: ~ 0.100 secs.
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
# Profiling: load sessionmaker: ~ 0.050 secs.
from sqlalchemy.orm import sessionmaker

from . import objects
from ...manager import BaseStore
from .managers.activity import ActivityManager
from .managers.category import CategoryManager
from .managers.fact import FactManager
from .managers.migrate import MigrationsManager
from .managers.tag import TagManager

__all__ = ('SQLAlchemyStore', )


class SQLAlchemyStore(BaseStore):
    """
    SQLAlchemy based backend.

    Unfortunately despite using SQLAlchemy some database specific settings can
    not be avoided (autoincrement, indexes etc).

    Some of those issues will not be relevant in later versions as we
    may get rid of Category and Activity ids entirely, just using their
    natural/composite keys as primary keys.

    However, for now we just support sqlite until the basic framework is up
    and running. It should take only minor but delayable effort to broaden the
    applicability to postgres, mysql and the likes.

    The main takeaway right now is, that their is no actual guarantee that
    in a distributed environment no race condition occur and we may end up
    with duplicate Category/Activity entries. No backend code will be able to
    prevent this by virtue of this being a DB issue.

    Furthermore, we will try hard to avoid placing more than one fact in a
    given time window. However, there can be no guarantee that in a distributed
    environment this will always work out. As a consequence, we make sure that
    all our single object data retrieval methods return only one item or throw
    an error alerting us about the inconsistency.
    """

    def __init__(self, config):
        """
        """
        super(SQLAlchemyStore, self).__init__(config)
        self.create_item_managers()

    def standup(self, session=None):
        """
        Set up the store.

        Args:
            config (dict): Dictionary of config key/value pairs.

            session (SQLALcheny Session object, optional): Provide a dedicated session
                to be used. Defaults to ``None``.

        Note:
            The ``session`` argument is mainly useful for tests.
        """
        engine = self.create_storage_engine()
        created_fresh = self.create_storage_tables(engine)
        self.initiate_storage_session(session, engine)
        if created_fresh:
            self.control_and_version_store()
        return created_fresh

    def cleanup(self):
        pass

    @property
    def db_url(self):
        """
        Create a ``database_url`` from ``config`` suitable to be consumed
        by ``create_engine``

        Our config may include:
            * ''db.engine``; Engine to be used.
            * ``db.host``; Host to connect to.
            * ``db.port``; Port to connect to.
            * ``db.path``; Used if ``engine='sqlite'``.
            * ``db.user``; Database user to be used for connection.
            * ``db.password``; Database user passwort to authenticate user.

        If ``db.engine='sqlite'`` you need to provide ``db.path`` as well.
        For any other engine ``db.host`` and ``db.name`` are mandatory.

        Note:
            * `SQLAlchemy docs
              <https://docs.sqlalchemy.org/en/latest/core/engines.html>`__

        Returns:
            str: ``database_url`` suitable to be consumed by ``create_engine``.

        Raises:
            ValueError: If a required config key/value pair is not present for
                the choosen ``db.engine``.
        """
        # [FIXME]
        # Contemplate if there are security implications that warrant sanitizing
        # config values.
        # (lb): This is an old hamster-lib comment. The user will be the ones
        # deliberately setting their config, so if their was a security concern
        # (SQL injection?), the user will have known what they've done.
        # - Can probably delete both these comments now.

        # Because ConfigDecorator, we could access variables with
        # dot-notation or by subscripting, e.g., these both work:
        #   engine = self.config['db.engine']
        #   engine = self.config['db']['engine']
        # The code generally uses dot-notation because that's how
        # the user sees it in `dob config dump` output; it's more
        # concise; and it's easier to bang out in a search command.
        engine = self.config['db.engine']
        host = self.config['db.host']
        name = self.config['db.name']
        path = self.config['db.path']
        port = self.config['db.port']
        user = self.config['db.user']
        password = self.config['db.password']

        if not engine:
            message = _("No engine found in config!")
            self.logger.error(message)
            raise ValueError(message)

        # URL composition is slightly different for sqlite
        if engine == 'sqlite':
            if not path:
                # We could have allowed for blank paths, which would make
                # SQLAlchemy default to ``:memory:``. But explicit is better
                # than implicit. You can still create an in memory db by passing
                # ``db_path=':memory:'`` deliberately.
                message = _("No 'db.path' found in config! Sqlite requires one.")
                self.logger.error(message)
                raise ValueError(message)
            if path != ':memory:':
                # Make sure we always use an absolute path.
                path = os.path.abspath(path)
            database_url = '{engine}:///{path}'.format(engine=engine, path=path)
        else:
            if not host:
                message = _(
                    "No 'db.host' found in config!"
                    " Engines other than sqlite require one."
                )
                self.logger.error(message)
                raise ValueError(message)
            if not name:
                message = _(
                    "No 'db.name' found in config!"
                    " Engines other than sqlite require one."
                )
                self.logger.error(message)
                raise ValueError(message)
            if not user:
                message = _(
                    "No 'db.user' found in config!"
                    " Engines other than sqlite require one."
                )
                self.logger.error(message)
                raise ValueError(message)
            if not password:
                message = _(
                    "No 'db.password' found in config!"
                    " Engines other than sqlite require one."
                )
                self.logger.error(message)
                raise ValueError(message)
            if port:
                port = ':{}'.format(port)
            database_url = (
                '{engine}://{user}:{password}@{host}{port}/{name}'
                .format(
                    engine=engine,
                    user=user,
                    password=password,
                    host=host,
                    port=port,
                    name=name,
                )
            )
        self.logger.debug(_('database_url: {}'.format(database_url)))
        return database_url

    def create_storage_engine(self):
        # [TODO]
        # It takes more deliberation to decide how to handle engine creation
        # if we receive a session. Should be require the session to bring
        # its own engine?
        engine = create_engine(self.db_url)
        self.logger.debug(_('Engine created.'))
        # NOTE: (lb): I succeeded at setting the ORM (Sqlite3) logger level,
        # but it didn't log anything (I was hoping to see all statements).
        #
        #  import logging
        #  engine.logger.setLevel(logging.DEBUG)
        return engine

    def create_storage_tables(self, engine):
        # Such magic: Stash the Engine() object in the SQLAlchemy package
        # where the Alchemy items will find it and use it by default.
        # - Per docs, store the object at objects.metadata.bind, where it can
        #   be "held globally for the lifetime of a single application...."
        #     https://docs.sqlalchemy.org/en/13/core/connections.html
        objects.metadata.bind = engine

        created_fresh = False
        try:
            # Create the database store at db_path.
            objects.metadata.create_all(engine, checkfirst=False)
            created_fresh = True
            self.logger.debug(_("Database tables created."))
        except OperationalError:
            # E.g., '(sqlite3.OperationalError) table categories already exists'.
            self.logger.debug(_("Database tables already exist."))
        return created_fresh

    def control_and_version_store(self):
        # (lb): I'm not sure how else to do this, or if this is "the way":
        #         Put the new database under migration control.
        latest_vers = self.migrations.latest_version()
        assert latest_vers is not None and latest_vers > 0
        self.migrations.control(version=latest_vers)

    def initiate_storage_session(self, session, engine):
        if not session:
            Session = sessionmaker(bind=engine)  # NOQA
            self.logger.debug(_("Bound engine to session-object."))
            self.session = Session()
            self.logger.debug(_("Instantiated session."))
        else:
            self.session = session

    def create_item_managers(self):
        self.migrations = MigrationsManager(self)
        self.categories = CategoryManager(self)
        self.activities = ActivityManager(self)
        self.tags = TagManager(self)
        localize = not self.config['time.tz_aware']
        self.facts = FactManager(self, localize=localize)
        self.fact_cls = None

