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
from nark.items.category import Category


class TestCategoryManager:
    """"""

    def test_add_new(self, alchemy_store, alchemy_category_factory):
        """
        Our manager methods return the persistant instance as hamster objects.
        As we want to make sure that we compare our expectations against the
        raw saved object, we look it up explicitly again.
        """
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        category = alchemy_category_factory.build().as_hamster(alchemy_store)
        category.pk = None
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        result = alchemy_store.categories._add(category)
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        db_instance = alchemy_store.session.query(AlchemyCategory).get(result.pk)
        assert category.equal_fields(db_instance)
        assert category != db_instance

    def test_add_existing_name(self, alchemy_store, alchemy_category_factory):
        """
        Make sure that adding a category with a name that is already present
        gives an error.
        """
        existing_category = alchemy_category_factory()
        category = alchemy_category_factory.build().as_hamster(alchemy_store)
        category.name = existing_category.name
        category.pk = None
        with pytest.raises(ValueError):
            alchemy_store.categories._add(category)

    def test_add_with_pk(self, alchemy_store, alchemy_category_factory):
        """
        Make sure that adding a alchemy_category that already got an PK
        raises an exception.
        """
        category = alchemy_category_factory().as_hamster(alchemy_store)
        category.name += "foobar"
        assert category.pk
        with pytest.raises(ValueError):
            alchemy_store.categories._add(category)

    def test_update(
        self,
        alchemy_store,
        alchemy_category_factory,
        new_category_values,
    ):
        """Test that updateing a alchemy_category works as expected."""
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        # (lb): NOTE_TO_SELF: The alchemy_category_factory fixture was created
        # when conftest.py called `register(lib_factories.CategoryFactory)`,
        # which, AFAICT, is the same as calling the factory directly:
        #   alchemy_category_factory = factories.AlchemyCategoryFactory
        category = alchemy_category_factory().as_hamster(alchemy_store)
        new_values = new_category_values(category)
        for key, value in new_values.items():
            assert getattr(category, key) != value
        for key, value in new_values.items():
            setattr(category, key, value)
        alchemy_store.categories._update(category)
        db_instance = alchemy_store.session.query(AlchemyCategory).get(category.pk)
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        assert category.equal_fields(db_instance)

    def test_update_without_pk(self, alchemy_store, alchemy_category_factory):
        """Make sure that passing a category without a PK raises an error."""
        category = alchemy_category_factory.build(pk=None).as_hamster(alchemy_store)
        with pytest.raises(ValueError):
            alchemy_store.categories._update(category)

    def test_update_invalid_pk(self, alchemy_store, alchemy_category_factory):
        """
        Make sure that passing a category with a non existing PK raises an error.
        """
        category = alchemy_category_factory().as_hamster(alchemy_store)
        category.pk = category.pk + 10
        with pytest.raises(KeyError):
            alchemy_store.categories._update(category)

    def test_update_existing_name(self, alchemy_store, alchemy_category_factory):
        """
        Make sure that renaming a given alchemy_category to a taken name
        throws an error.
        """
        category_1, category_2 = (
            alchemy_category_factory(),
            alchemy_category_factory(),
        )
        category_2 = category_2.as_hamster(alchemy_store)
        category_2.name = category_1.name
        with pytest.raises(ValueError):
            alchemy_store.categories._update(category_2)

    def test_remove(self, alchemy_store, alchemy_category_factory):
        """Make sure passing a valid alchemy_category removes it from the db."""
        alchemy_category = alchemy_category_factory()
        category = alchemy_category.as_hamster(alchemy_store)
        alchemy_store.categories.remove(category)
        assert alchemy_store.session.query(AlchemyCategory).get(category.pk) is None

    def test_remove_no_pk(self, alchemy_store, alchemy_category_factory):
        """Ensure that passing a alchemy_category without an PK raises an error."""
        category = alchemy_category_factory.build(pk=None).as_hamster(alchemy_store)
        with pytest.raises(ValueError):
            alchemy_store.categories.remove(category)

    def test_remove_invalid_pk(self, alchemy_store, alchemy_category_factory):
        """Ensure that passing a alchemy_category without an PK raises an error."""
        category = alchemy_category_factory.build(pk=800).as_hamster(alchemy_store)
        with pytest.raises(KeyError):
            alchemy_store.categories.remove(category)

    def test_get_existing_pk(self, alchemy_store, alchemy_category_factory):
        """Make sure method retrieves corresponding object."""
        category = alchemy_category_factory().as_hamster(alchemy_store)
        result = alchemy_store.categories.get(category.pk)
        assert result == category

    def test_get_non_existing_pk(self, alchemy_store, alchemy_category_factory):
        """Make sure we throw an error if PK can not be resolved."""
        alchemy_store.session.query(AlchemyCategory).count == 0
        category = alchemy_category_factory()
        alchemy_store.session.query(AlchemyCategory).count == 1
        with pytest.raises(KeyError):
            alchemy_store.categories.get(category.pk + 1)

    def test_get_by_name(self, alchemy_category_factory, alchemy_store):
        """Make sure a alchemy_category can be retrieved by name."""
        category = alchemy_category_factory().as_hamster(alchemy_store)
        result = alchemy_store.categories.get_by_name(category.name)
        assert result == category

    def test_get_all(self, alchemy_store, set_of_categories):
        results = alchemy_store.categories.get_all()
        assert len(results) == len(set_of_categories)
        assert len(results) == alchemy_store.session.query(AlchemyCategory).count()
        for category in set_of_categories:
            assert category.as_hamster(alchemy_store) in results

    # Test convenience methods.
    def test_get_or_create_get(self, alchemy_store, alchemy_category_factory):
        """
        Test that if we pass a alchemy_category of existing name, we just
        return it.
        """
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        category = alchemy_category_factory().as_hamster(alchemy_store)
        result = alchemy_store.categories.get_or_create(category)
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        assert result == category

    def test_get_or_create_new_name(self, alchemy_store, alchemy_category_factory):
        """
        Make sure that passing a category with new name creates and returns
        new instance.
        """
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        category = alchemy_category_factory.build().as_hamster(alchemy_store)
        category.pk = None
        result = alchemy_store.categories.get_or_create(category)
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        assert result.equal_fields(category)

    def test_get_deleted_item(self, alchemy_store, alchemy_category):
        """Make sure method retrieves deleted object."""
        alchemy_category.deleted = True
        result = alchemy_store.categories.get(alchemy_category.pk, deleted=True)
        assert result == alchemy_category

    def test_get_all_match_categories(
        self,
        alchemy_store,
        set_of_alchemy_facts_active,
        alchemy_category_factory,
    ):
        """Test get_all argument: QueryTerms.match_activities."""
        category_0 = set_of_alchemy_facts_active[0].activity.category
        category_2 = set_of_alchemy_facts_active[2].activity.category.name
        any_category = alchemy_category_factory(pk=None)
        category_with_pk_None = Category(name=any_category.name)
        results = alchemy_store.categories.get_all(
            match_categories=[
                category_0,
                category_2,
                category_with_pk_None,
                None,
            ],
        )
        assert len(results) == 3

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
        ),
    )
    def test_get_all_sort_cols(self, alchemy_store, sort_cols):
        alchemy_store.categories.get_all(sort_cols=sort_cols)

    def test_get_all_sort_cols_tag_fails(self, alchemy_store, mocker):
        # The tag table is not joined for Activity query.
        mocker.patch.object(alchemy_store.logger, "warning")
        alchemy_store.categories.get_all(sort_cols=["tag"])
        assert alchemy_store.logger.warning.called

    def test_get_all_sort_cols_unknown(self, alchemy_store, mocker):
        mocker.patch.object(alchemy_store.logger, "warning")
        alchemy_store.categories.get_all(sort_cols=["foo"])
        assert alchemy_store.logger.warning.called
