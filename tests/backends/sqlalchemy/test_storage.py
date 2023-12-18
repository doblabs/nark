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

import pytest

from nark.backends.sqlalchemy.objects import AlchemyCategory
from nark.backends.sqlalchemy.storage import SQLAlchemyStore
from nark.config import decorate_config

# isort: off / Otherwise isort removes one of the following blank lines,
# but it doesn't if you remove the comment atop the following class.


# The reason we see a great deal of count == 0 statements is to make sure that
# db rollback works as expected. Once we are confident in our sqlalchemy/pytest
# setup those are not really needed.
class TestStore(object):
    """Tests to make sure our store/test setup behaves as expected."""

    def test_build_is_not_persistent(self, alchemy_store, alchemy_category_factory):
        """
        Make sure that calling ``factory.build()`` does not create a
        persistent db entry.
        """
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        alchemy_category_factory.build()
        assert alchemy_store.session.query(AlchemyCategory).count() == 0

    def test_factory_call_persistent(self, alchemy_store, alchemy_category_factory):
        """Make sure that ``factory()`` does creates a persistent db entry."""
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        alchemy_category_factory()
        assert alchemy_store.session.query(AlchemyCategory).count() == 1

    def test_create_is_persistent(self, alchemy_store, alchemy_category_factory):
        """Make sure that  ``create()`` does creates a persistent db entry."""
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        alchemy_category_factory()
        assert alchemy_store.session.query(AlchemyCategory).count() == 1

    def test_build_pk(self, alchemy_store, alchemy_category_factory):
        """Make sure that factory instances have no pk assigned."""
        instance = alchemy_category_factory.build()
        assert instance.pk

    def test_create_pk(self, alchemy_store, alchemy_category_factory):
        """Make sure that factory.create instances have pk assigned."""
        instance = alchemy_category_factory.create()
        assert instance.pk

    def test_instance_fixture(self, alchemy_store, alchemy_category):
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        assert alchemy_category.pk
        assert alchemy_category.name

    def test_get_db_url(self, alchemy_config_parametrized, alchemy_store):
        """Make sure that db_url composition works as expected."""
        config, expectation = alchemy_config_parametrized
        alchemy_store.config = decorate_config(config)
        assert alchemy_store.db_url == expectation

    def test_get_db_url_missing_keys(
        self,
        alchemy_config_missing_store_config_parametrized,
        alchemy_store,
    ):
        """
        Make sure that db_url composition throws error if key/values are
        missing in config.
        """
        with pytest.raises(ValueError):
            alchemy_store.config = decorate_config(
                alchemy_config_missing_store_config_parametrized
            )
            # If decorate_config() does not raise on engine missing error,
            # db_url will raise on missing path, host, etc.
            alchemy_store.db_url

    def test_init_with_unicode_path(self, alchemy_config, db_path_parametrized):
        """Test that Instantiating a store with a unicode path works."""
        alchemy_config["db.path"] = db_path_parametrized
        assert SQLAlchemyStore(alchemy_config)
