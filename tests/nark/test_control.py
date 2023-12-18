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

import logging

import pytest

import nark
from nark import get_version
from nark.manager import BaseStore


class TestController:
    @pytest.mark.parametrize("storetype", ["sqlalchemy"])
    def test_get_store_valid(self, controller, storetype):
        """Make sure we receive a valid ``store`` instance."""
        # [TODO]
        # Once we got backend registration up and running this should be
        # improved to check actual store type for that backend.
        controller.config["db"]["orm"] = storetype
        assert isinstance(controller._get_store(), BaseStore)

    def test_get_store_invalid(self, controller):
        """Make sure we get an exception if store retrieval fails."""
        # Because of config validation, as opposed to hamster-lib,
        # you cannot set the config to bad values, i.e., the code
        # fails before we're able to call, says, controller._get_store().
        with pytest.raises(ValueError):
            controller.config["db"]["orm"] = None

    def test_update_config(self, controller, base_config, mocker):
        """Make sure we assign new config and get a new store."""
        mocker.patch.object(controller, "_get_store")
        controller.update_config(base_config)
        assert controller.config.as_dict() == base_config
        assert controller._get_store.called

    def test_get_logger(self, controller):
        """Make sure we recieve a logger that maches our expectations."""
        logger = controller._get_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "nark.log"
        # [FIXME]
        # assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.NullHandler)

    def test_sql_logger(self, controller):
        """Make sure we recieve a logger that maches our expectations."""
        logger = controller._sql_logger()
        assert isinstance(logger, logging.Logger)
        assert logger.name == "nark.store"
        assert isinstance(logger.handlers[0], logging.NullHandler)


class TestNarkLib:
    def test_get_version_argless(self):
        # (lb): Not sure how best to test get_version, because it
        # behaves differently if setuptools_scm is included or not,
        # and the version will often be a non-release version, e.g.,
        # '3.0.2.dev9+gfba2058.d20200401'. For now, just say not empty.
        assert get_version() != ""

    def test_get_version_include_head_normal(self):
        result = get_version(include_head=True)
        # (lb): I'd rather not encode the version number anywhere in code
        # (that's why we use setuptools_scm!), but also don't expect to
        # upgrade to v.4 anytime soon.
        assert result.startswith("3.")
        # The repo version is appended in (parentheses), which we'll test next;
        # this test is meant to provide coverage of _version_from_tags, but we
        # won't know what the local repo version is, or even if it's different
        # from the tagged version.
