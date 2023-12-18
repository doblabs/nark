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

from nark.backends.sqlalchemy.objects import AlchemyTag


class TestTagManager:
    """"""

    def test_add_new(self, alchemy_store, alchemy_tag_factory):
        """
        Our manager methods return the persistant instance as hamster objects.
        As we want to make sure that we compare our expectations against the
        raw saved object, we look it up explicitly again.
        """
        assert alchemy_store.session.query(AlchemyTag).count() == 0
        tag = alchemy_tag_factory.build().as_hamster(alchemy_store)
        tag.pk = None
        assert alchemy_store.session.query(AlchemyTag).count() == 0
        result = alchemy_store.tags._add(tag)
        assert alchemy_store.session.query(AlchemyTag).count() == 1
        db_instance = alchemy_store.session.query(AlchemyTag).get(result.pk)
        assert tag.equal_fields(db_instance)
        assert tag != db_instance

    def test_add_existing_name(self, alchemy_store, alchemy_tag_factory):
        """
        Make sure that adding a tag with a name that is already present
        gives an error.
        """
        existing_tag = alchemy_tag_factory()
        tag = alchemy_tag_factory.build().as_hamster(alchemy_store)
        tag.name = existing_tag.name
        tag.pk = None
        with pytest.raises(ValueError):
            alchemy_store.tags._add(tag)

    def test_add_with_pk(self, alchemy_store, alchemy_tag_factory):
        """
        Make sure that adding a alchemy_tag that already got an PK raises
        an exception.
        """
        tag = alchemy_tag_factory().as_hamster(alchemy_store)
        tag.name += "foobar"
        assert tag.pk
        with pytest.raises(ValueError):
            alchemy_store.tags._add(tag)

    def test_update(self, alchemy_store, alchemy_tag_factory, new_tag_values):
        """Test that updateing a alchemy_tag works as expected."""
        alchemy_store.session.query(AlchemyTag).count() == 0
        tag = alchemy_tag_factory().as_hamster(alchemy_store)
        new_values = new_tag_values(tag)
        for key, value in new_values.items():
            assert getattr(tag, key) != value
        for key, value in new_values.items():
            setattr(tag, key, value)
        alchemy_store.tags._update(tag)
        db_instance = alchemy_store.session.query(AlchemyTag).get(tag.pk)
        assert alchemy_store.session.query(AlchemyTag).count() == 1
        assert tag.equal_fields(db_instance)

    def test_update_without_pk(self, alchemy_store, alchemy_tag_factory):
        """Make sure that passing a tag without a PK raises an error."""
        tag = alchemy_tag_factory.build(pk=None).as_hamster(alchemy_store)
        with pytest.raises(ValueError):
            alchemy_store.tags._update(tag)

    def test_update_invalid_pk(self, alchemy_store, alchemy_tag_factory):
        """Make sure that passing a tag with a non existing PK raises an error."""
        tag = alchemy_tag_factory().as_hamster(alchemy_store)
        tag.pk = tag.pk + 10
        with pytest.raises(KeyError):
            alchemy_store.tags._update(tag)

    def test_update_existing_name(self, alchemy_store, alchemy_tag_factory):
        """
        Make sure that renaming a given alchemy_tag to a taken name throws an error.
        """
        tag_1, tag_2 = (alchemy_tag_factory(), alchemy_tag_factory())
        tag_2 = tag_2.as_hamster(alchemy_store)
        tag_2.name = tag_1.name
        with pytest.raises(ValueError):
            alchemy_store.tags._update(tag_2)

    def test_remove(self, alchemy_store, alchemy_tag_factory):
        """Make sure passing a valid alchemy_tag removes it from the db."""
        tag = alchemy_tag_factory().as_hamster(alchemy_store)
        alchemy_store.tags.remove(tag)
        assert alchemy_store.session.query(AlchemyTag).get(tag.pk) is None

    def test_remove_no_pk(self, alchemy_store, alchemy_tag_factory):
        """Ensure that passing a alchemy_tag without an PK raises an error."""
        tag = alchemy_tag_factory.build(pk=None).as_hamster(alchemy_store)
        with pytest.raises(ValueError):
            alchemy_store.tags.remove(tag)

    def test_remove_invalid_pk(self, alchemy_store, alchemy_tag_factory):
        """Ensure that passing a alchemy_tag without an PK raises an error."""
        tag = alchemy_tag_factory.build(pk=800).as_hamster(alchemy_store)
        with pytest.raises(KeyError):
            alchemy_store.tags.remove(tag)

    def test_get_existing_pk(self, alchemy_store, alchemy_tag_factory):
        """Make sure method retrieves corresponding object."""
        tag = alchemy_tag_factory().as_hamster(alchemy_store)
        result = alchemy_store.tags.get(tag.pk)
        assert result == tag

    def test_get_non_existing_pk(self, alchemy_store, alchemy_tag_factory):
        """Make sure we throw an error if PK can not be resolved."""
        alchemy_store.session.query(AlchemyTag).count == 0
        tag = alchemy_tag_factory()
        alchemy_store.session.query(AlchemyTag).count == 1
        with pytest.raises(KeyError):
            alchemy_store.tags.get(tag.pk + 1)

    def test_get_by_name(self, alchemy_tag_factory, alchemy_store):
        """Make sure a alchemy_tag can be retrieved by name."""
        tag = alchemy_tag_factory().as_hamster(alchemy_store)
        result = alchemy_store.tags.get_by_name(tag.name)
        assert result == tag

    def test_get_all(self, alchemy_store, set_of_tags):
        results = alchemy_store.tags.get_all()
        assert len(results) == len(set_of_tags)
        assert len(results) == alchemy_store.session.query(AlchemyTag).count()
        for tag in set_of_tags:
            assert tag.as_hamster(alchemy_store) in results

    # Test convenience methods.
    def test_get_or_create_get(self, alchemy_store, alchemy_tag_factory):
        """
        Test that if we pass a alchemy_tag of existing name, we just return it.
        """
        assert alchemy_store.session.query(AlchemyTag).count() == 0
        tag = alchemy_tag_factory().as_hamster(alchemy_store)
        result = alchemy_store.tags.get_or_create(tag)
        assert alchemy_store.session.query(AlchemyTag).count() == 1
        assert result == tag

    def test_get_or_create_new_name(self, alchemy_store, alchemy_tag_factory):
        """
        Make sure that passing a tag with new name creates and returns new instance.
        """
        assert alchemy_store.session.query(AlchemyTag).count() == 0
        tag = alchemy_tag_factory.build().as_hamster(alchemy_store)
        tag.pk = None
        result = alchemy_store.tags.get_or_create(tag)
        assert alchemy_store.session.query(AlchemyTag).count() == 1
        assert result.equal_fields(tag)

    def test_get_deleted_item(self, alchemy_store, alchemy_tag):
        """Make sure method retrieves deleted object."""
        alchemy_tag.deleted = True
        result = alchemy_store.tags.get(alchemy_tag.pk, deleted=True)
        assert result == alchemy_tag

    def test_get_all_match_tags(self, alchemy_store, set_of_alchemy_facts_active):
        """Test get_all argument: QueryTerms.match_tags."""
        # Note that non-Fact query does not actually implement the
        # QueryTerms.query_filter_by_tags option (because no obvious
        # use case). But QueryTerms still accepts it.
        results = alchemy_store.tags.get_all(
            match_tags=["foo"],
        )
        expect_all_tags = 0
        for fact in set_of_alchemy_facts_active:
            expect_all_tags += len(fact.tags)
        assert len(results) == expect_all_tags

    # ***

    @pytest.mark.parametrize(
        ("sort_cols"),
        (
            (["start"]),
            ([None]),
            (["usage"]),
            (["time"]),
            (["activity"]),
            (["category"]),
            (["tag"]),
        ),
    )
    def test_get_all_sort_cols(self, alchemy_store, sort_cols):
        alchemy_store.tags.get_all(sort_cols=sort_cols)

    def test_get_all_sort_cols_unknown(self, alchemy_store, mocker):
        mocker.patch.object(alchemy_store.logger, "warning")
        alchemy_store.tags.get_all(sort_cols=["foo"])
        assert alchemy_store.logger.warning.called
