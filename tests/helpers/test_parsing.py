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

import pytest
from unittest.mock import patch

from freezegun import freeze_time

from nark.helpers.parsing import (
    parse_factoid,
    Parser,
    ParserMissingActivityException,
    ParserMissingDatetimeTwoException,
    ParserMissingSeparatorActivity,
)

from nark.tests.helpers.conftest import factoid_fixture

# See also parser testing via Fact.create_from_factoid in tests/items/test_fact.py
# and also Factoid parsing start/end resolution in dob/tests/fact/test_add_fact.py.


@pytest.fixture
def parser():
    return Parser()


class TestParser(object):
    def test_parser_to_str(self, parser):
        assert str(parser).startswith("raw: ")

    def test_parser_factoid_None(self, parser):
        """Test that Factoid parser fails if Activity not indicated."""
        # That is, a Factoid is at least an Activity.
        with pytest.raises(ParserMissingActivityException):
            parser.dissect_raw_fact(factoid=None)

    def test_parser_factoid_list(self, parser):
        parser.dissect_raw_fact(factoid=["01:00 to 03:00 act @"])

    def test_parser_factoid_activity_with_sep(self, parser):
        parser.dissect_raw_fact(factoid="yesterday until 03:00 act @")

    def test_parser_factoid_activity_without_sep(self, parser):
        with pytest.raises(ParserMissingSeparatorActivity):
            parser.dissect_raw_fact(factoid="yesterday: act", time_hint="verify_end")

    # Test single entry DATE_TO_DATE_SEPARATORS__RAW.
    @patch("nark.helpers.parsing.DATE_TO_DATE_SEPARATORS__RAW", ["to"])
    def test_parser_factoid_missing_two_single_sep(self, parser):
        with pytest.raises(ParserMissingDatetimeTwoException):
            parser.dissect_raw_fact("13:00: foo@bar", "verify_both")

    @freeze_time("2015-12-25 18:00")
    @pytest.mark.parametrize(*factoid_fixture)
    def test_helpers_parsing_parse_factoid(
        self,
        parser,
        raw_fact,
        time_hint,
        expectation,
    ):
        """Make sure that a valid raw fact creates a proper Fact."""
        fact_dict, err = parse_factoid(
            raw_fact,
            time_hint=time_hint,
            lenient=True,
        )
        if "err" in expectation and expectation["err"]:
            assert str(err).startswith(expectation["err"])
        else:
            assert fact_dict["start"] == expectation["start_raw"]
            assert fact_dict["end"] == expectation["end_raw"]
            assert fact_dict["activity"] == expectation["activity"]
            assert fact_dict["category"] == expectation["category"]
            assert fact_dict["tags"] == expectation["tags"]
            assert fact_dict["description"] == expectation["description"]
            assert fact_dict["warnings"] == expectation["warnings"]
