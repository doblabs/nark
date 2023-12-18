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

from nark.helpers import logging as logging_helpers


class TestSetupHandler(object):
    def test_get_formatter_basic(self, mocker):
        """Test formatter fetcher."""
        formatter = logging_helpers.formatter_basic()
        # (lb): Is this legit, or a little too _intimate?
        expected = "[%(levelname)s] %(asctime)s %(name)s %(funcName)s: %(message)s"
        assert formatter._fmt == expected

    def test_setup_handler_stream_handler(self, mocker):
        """Test logging setup."""
        stream_handler = logging.StreamHandler()
        formatter = logging_helpers.formatter_basic()
        logger = mocker.MagicMock()
        logging_helpers.setup_handler(stream_handler, formatter, logger)
        logger.addHandler.assert_called_with(stream_handler)
