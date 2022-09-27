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
from datetime import datetime

from easy_as_pypi_appdirs import AppDirs

from .config import decorate_config
from .helpers import logging as logging_helpers
from .managers.activity import BaseActivityManager
from .managers.category import BaseCategoryManager
from .managers.fact import BaseFactManager
from .managers.tag import BaseTagManager

__all__ = ('BaseStore', )


class BaseStore(object):
    """
    A controller store defines the interface to interact with stored entities,
    regardless of the backend being used.
    """

    def __init__(self, config):
        self.config = decorate_config(config)
        self.init_config()
        self.init_logger()
        self._now = None
        self.add_pytest_managers()

    def add_pytest_managers(self):
        if not os.environ.get('PYTEST_CURRENT_TEST', None):
            return
        # The following intermediate classes are solely used for testing!
        self.categories = BaseCategoryManager(self)
        self.activities = BaseActivityManager(self)
        self.tags = BaseTagManager(self)
        localize = not self.config['time.tz_aware']
        self.facts = BaseFactManager(self, localize=localize)

    def standup(self):
        """
        Any backend specific setup code that needs to be executed before
        the data store can be used (including creating the data store).
        """
        raise NotImplementedError

    def cleanup(self):
        """
        Any backend specific teardown code that needs to be executed before
        we shut down gracefully.
        """
        raise NotImplementedError

    def init_config(self):
        self.config.setdefault('db.orm', 'sqlalchemy')
        self.config.setdefault('db.engine', 'sqlite')
        self.config.setdefault('db.path', self.default_db_path)
        self.config.setdefault('db.host', '')
        self.config.setdefault('db.port', '')
        self.config.setdefault('db.name', '')
        self.config.setdefault('db.user', '')
        self.config.setdefault('db.password', '')
        self.config.setdefault('time.allow_momentaneous', False)
        self.config.setdefault('time.day_start', '')
        self.config.setdefault('time.fact_min_delta', '0')
        self.config.setdefault('dev.catch_errors', False)
        self.config.setdefault('dev.lib_log_level', 'WARNING')
        self.config.setdefault('dev.sql_log_level', 'WARNING')
        self.config.setdefault('time.tz_aware', False)
        self.config.setdefault('time.default_tzinfo', '')

    @property
    def default_db_path(self):
        if not AppDirs.is_ready:
            return ''
        db_path = os.path.join(
            AppDirs().user_data_dir,
            # (lb): Whatever client is using the nark library
            # will generally setup db_path specially; this is
            # just a default filename for completeness.
            'dob.sqlite',
        )
        return db_path

    def init_logger(self):
        sql_log_level = self.config['dev.sql_log_level']
        self.logger = logging_helpers.set_logger_level(
            'nark.store', sql_log_level,
        )

    @property
    def now(self):
        # Use the same 'now' for all items that need it. 'Now' is considered
        # the run of the whole command, and not different points within it.
        # (lb): It probably doesn't matter either way what we do, but I'd
        # like all facts that use now to reflect the same moment in time,
        # rather than being microseconds apart from one another.
        # (lb): Also, we use @property to convey to the caller that this
        # is not a function; i.e., the value is static, not re-calculated.
        if self._now is None:
            self._now = self.now_tz_aware()
        return self._now

    def now_refresh(self):
        self._now = None
        return self.now

    def now_tz_aware(self):
        if self.config['time.tz_aware']:
            # FIXME/2018-05-23: (lb): Tests use utcnow(). Should they honor tz_aware?
            #   (Though if Freezegun being used, now() == utcnow().)
            # Clear microseconds to avoid six digits of noise, e.g., 12:34:56.789012.
            # (lb): I added seconds to hamster (was historically demarcated by minutes),
            # because I think seconds could be useful to a developer. But not no more.
            return datetime.utcnow().replace(microsecond=0)
        else:
            return datetime.now().replace(microsecond=0)

