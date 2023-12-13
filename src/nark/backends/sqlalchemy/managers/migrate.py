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

import os

import lazy_import
from ....helpers.legacy_db import upgrade_legacy_db_hamster_applet
from ....managers.migrate import BaseMigrationsManager

from nark.backends.sqlalchemy import objects

# Profiling: Loading `migrate` takes ~ 0.090 seconds.
migrate_exceptions = lazy_import.lazy_module(
    'sqlalchemy_migrate_hotoffthehamster.exceptions'
)
migrate_versioning_cfgparse = lazy_import.lazy_module(
    'sqlalchemy_migrate_hotoffthehamster.versioning.cfgparse'
)
migrate_versioning_api = lazy_import.lazy_module(
    'sqlalchemy_migrate_hotoffthehamster.versioning.api'
)

__all__ = ('MigrationsManager', )


class MigrationsManager(BaseMigrationsManager):
    """"""

    @property
    def basepath(self):
        return self.migrations_path()

    @property
    def config(self):
        return self.migrations_config()

    # ***

    # - Prefer using an existing SQLAlchemy Engine, rather than opening the URL.
    # - The migrate class accepts either a database URL, or an existing Engine
    #   object. Given a path, the migrate_versioning package will just open a
    #   new connection to the URL, which works fine for files on disk or actual
    #   URLs on the net. But for tests, especially those run via CliRunner where
    #   it's more difficult to mock or otherwise skip normal initialization code,
    #   use the existing Engine object.
    #   - This supports using an SQLite store in :memory:, for which there is no
    #     other way to connect to the same database other than through the Engine
    #     ((lb): At least, not that I know of; and makes sense there wouldn't be).
    # - Note that using CliRunner poses a challenge with passing variables, and
    #   test variables that need to be applied to the Click code under test
    #   generally need to be applied using a MagicMock or a PropertyMock. However,
    #   the Engine is already always available at a global location (at least the
    #   way we've got our code wired, which follows convention), so rather than
    #   mock it in, we just always look for the existing Engine, even in production.
    #   - The SQLAlchemy Engine object is stashed at objects.metadata.bind, and is
    #     meant to be "held globally for the lifetime of a single application...."
    #       https://docs.sqlalchemy.org/en/13/core/connections.html
    @property
    def engine_or_url(self):
        return objects.metadata.bind or self.store.db_url

    # ***

    def control(self, version=None, engine=None):
        """Mark a database as under version control."""
        current_ver = self.version()
        if current_ver is None:
            url = self.engine_or_url
            try:
                migrate_versioning_api.version_control(
                    url, self.basepath, version=version, config=self.config,
                )
                return True
            except migrate_exceptions.DatabaseAlreadyControlledError:
                return False
        elif current_ver == 0:
            return False
        else:
            return None

    def downgrade(self):
        """Downgrade the database according to its migration version."""
        current_ver = self.version()
        if current_ver is None:
            return None
        latest_ver = migrate_versioning_api.version(
            self.basepath, config=self.config,
        )
        if not latest_ver:
            return None
        assert current_ver <= latest_ver
        if current_ver > 0:
            next_version = current_ver - 1
            url = self.engine_or_url
            migrate_versioning_api.downgrade(
                url, self.basepath, version=next_version, config=self.config,
            )
            return True
        else:
            return False

    def upgrade(self):
        """Upgrade the database according to its migration version."""
        current_ver = self.version()
        if current_ver is None:
            return None
        latest_ver = migrate_versioning_api.version(
            self.basepath, config=self.config,
        )
        if not latest_ver:
            return None
        assert current_ver <= latest_ver
        if current_ver < latest_ver:
            next_version = current_ver + 1
            url = self.engine_or_url
            migrate_versioning_api.upgrade(
                url, self.basepath, version=next_version, config=self.config,
            )
            return True
        else:
            return False

    def version(self):
        """Returns the current migration of the active database."""
        url = self.engine_or_url
        try:
            return migrate_versioning_api.db_version(
                url, self.basepath, config=self.config,
            )
        except migrate_exceptions.DatabaseNotControlledError:
            return None

    def latest_version(self):
        """Returns the latest version defined by the application."""
        try:
            repo_latest = migrate_versioning_api.version(
                self.basepath, config=self.config,
            )
            return int(repo_latest.value)
        except migrate_exceptions.DatabaseNotControlledError:
            return None

    # ***

    def migrations_config(self):
        """Return sqlalchemy-migrate migrate.cfg a hot-n-ready config object."""
        # See nark/migrations/migrate.cfg.example for descriptions.
        config = migrate_versioning_cfgparse.Parser()
        config['db_settings'] = {}
        config['db_settings']['repository_id'] = 'nark-migrations'
        config['db_settings']['version_table'] = 'migrate_version'
        config['db_settings']['required_dbs'] = '[]'
        config['db_settings']['use_timestamp_numbering'] = 'False'
        return config

    def migrations_path(self):
        # (lb): This is a little awkward. But there's not
        # another convenient way to do this, is there?
        path = os.path.abspath(
            os.path.join(
                # Meh. We could also do dirname(nark.__file__) and use fewer ..'s.
                #    path = os.path.join(os.path.dirname(nark.__file__), 'migrations')
                # except that nark is not a package, it's this package!
                os.path.dirname(__file__),
                '../../../migrations',
            )
        )
        return path

    # ***

    def legacy_upgrade_from_hamster_applet(self, db_path):
        upgrade_legacy_db_hamster_applet(db_path)

    def legacy_upgrade_from_hamster_lib(self):
        # (lb): I'm not sure how much traction hamster-lib had.
        #  So I'm not sure this function is needed.
        #  And hamster-libbers out there need a hand?
        #  You'll need to rename 3 things is all, I'm sure:
        #    Table renamed: facttags → fact_tags
        #    Cols renamed: facts.start_time/end_time → facts.start/end
        #  Please open a ticket if you really want this feature!
        raise NotImplementedError

