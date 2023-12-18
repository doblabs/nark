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

from nark.backends.sqlalchemy.objects import AlchemyActivity, AlchemyCategory
from nark.items.activity import Activity


class TestActivityManager:
    """"""

    def test_get_or_create_get(self, alchemy_store, alchemy_activity):
        """
        Make sure that passing an existing activity retrieves the corresponding
        instance.

        Note:
            * The activity will is be looked up by its composite key, so not to
            make any assumptions on the existence of a PK.
        """
        activity = alchemy_activity.as_hamster(alchemy_store)
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        result = alchemy_store.activities.get_or_create(activity)
        assert result == activity
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1

    def test_get_or_create_new(self, alchemy_store, activity):
        """
        Make sure that passing a new activity create a new persitent instance.

        Note:
            * The activity will is be looked up by its composite key, so not to
            make any assumptions on the existence of a PK.
        """
        assert alchemy_store.session.query(AlchemyActivity).count() == 0
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        result = alchemy_store.activities.get_or_create(activity)
        assert result.equal_fields(activity)
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1

    def test_save_new(self, activity, alchemy_store):
        """Make sure that saving a new activity add a new persistent instance."""
        # [TODO]
        # This should not be needed as ``save`` is a basestore method.
        # Its just a case of 'better save than sorry.
        assert activity.pk is None
        count_before = alchemy_store.session.query(AlchemyActivity).count()
        result = alchemy_store.activities._add(activity)
        count_after = alchemy_store.session.query(AlchemyActivity).count()
        assert count_before < count_after
        assert result.equal_fields(activity)

    def test_save_existing(
        self,
        alchemy_store,
        alchemy_activity,
        alchemy_category_factory,
    ):
        """
        Make sure that saving an existing activity add no new persistent
        instance.
        """
        # [TODO]
        # This should not be needed as ``save`` is a basestore method.
        activity = alchemy_activity.as_hamster(alchemy_store)
        activity.category = alchemy_category_factory()
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 2
        result = alchemy_store.activities.save(activity)
        assert result == activity
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 2

    def test_activity_without_category(self, alchemy_store, activity):
        """Add a new activity without an category."""
        activity.category = None
        result = alchemy_store.activities._add(activity)
        assert result.equal_fields(activity)

    def test_add_new_with_new_category(self, alchemy_store, activity, category):
        """
        Test that adding a new alchemy_activity with new alchemy_category
        creates both.
        """
        assert alchemy_store.session.query(AlchemyActivity).count() == 0
        assert alchemy_store.session.query(AlchemyCategory).count() == 0
        activity.category = category
        result = alchemy_store.activities._add(activity)
        db_instance = alchemy_store.session.query(AlchemyActivity).get(result.pk)
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        assert db_instance.as_hamster(alchemy_store).equal_fields(activity)

    def test_add_new_with_existing_category(
        self,
        alchemy_store,
        activity,
        alchemy_category,
    ):
        """
        Test that adding a new activity with existing category does not
        create a new one.
        """
        activity.category = alchemy_category.as_hamster(alchemy_store)
        assert alchemy_store.session.query(AlchemyActivity).count() == 0
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        result = alchemy_store.activities._add(activity)
        db_instance = alchemy_store.session.query(AlchemyActivity).get(result.pk)
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        assert db_instance.as_hamster(alchemy_store).equal_fields(activity)

    def test_add_new_with_existing_name_and_alchemy_category(
        self,
        alchemy_store,
        activity,
        alchemy_activity,
    ):
        """
        Test that adding a new alchemy_activity_with_existing_composite_key
        throws error.
        """
        activity.name = alchemy_activity.name
        activity.category = alchemy_activity.category.as_hamster(alchemy_store)
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        with pytest.raises(ValueError):
            alchemy_store.activities._add(activity)
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1

    def test_add_with_pk(self, alchemy_store, activity):
        """Make sure that adding an alchemy_activity with a PK raises error."""
        activity.pk = 234
        with pytest.raises(ValueError):
            alchemy_store.activities._add(activity)

    # *** ._update() method tests.

    def test_update_without_pk(self, alchemy_store, activity):
        """Make sure that calling update without a PK raises exception."""
        with pytest.raises(ValueError) as excinfo:
            alchemy_store.activities._update(activity)
        assert str(excinfo.value).startswith("The Activity passed")

    def test_update_with_existing_name_and_new_category_name(
        self,
        alchemy_store,
        activity,
        alchemy_activity,
        alchemy_category_factory,
    ):
        """
        Make sure that calling update on existing composite key raises exception.
        """
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1

        assert activity.pk is None
        activity.pk = alchemy_activity.pk
        activity.name = alchemy_activity.name

        category = alchemy_category_factory()
        assert alchemy_activity.category != category
        assert activity.category.pk is None
        # And now for something completely different.
        activity.category.name = category.name

        result = alchemy_store.activities._update(activity)
        # The result is almost the same as what we gave it -- except now
        # the category PK will have been assigned, check it:
        activity.category.pk = result.category.pk
        assert result == activity

    def test_update_fails_on_existing_activity_category_conflict(
        self,
        alchemy_store,
        activity,
        alchemy_activity,
        alchemy_category,
    ):
        """
        Make sure that calling update on existing composite key raises exception.
        """
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 1
        # (lb): Interesting. Or maybe not? Did not expect fixture item object to be
        # same as the one in the fixture store, especially because both the activity
        # and the category exist in store whether or not also specified as a fixture.
        stored_activity = alchemy_store.session.query(AlchemyActivity).one()
        assert id(stored_activity) == id(alchemy_activity)
        assert id(stored_activity.category) == id(alchemy_category)

        assert activity.pk is None
        activity.pk = alchemy_activity.pk
        activity.name = alchemy_activity.name
        activity.category.name = alchemy_category.name

        with pytest.raises(ValueError) as excinfo:
            alchemy_store.activities._update(activity)
        assert str(excinfo.value).startswith("The database already contains that")

    def test_update_with_existing_category_name_conflict_again(
        self,
        alchemy_store,
        alchemy_activity,
        alchemy_category_factory,
    ):
        activity = alchemy_activity.as_hamster(alchemy_store)
        category = alchemy_category_factory().as_hamster(alchemy_store)
        activity.category = category
        alchemy_store.activities._update(activity)
        with pytest.raises(ValueError) as excinfo:
            # 2nd time's a no-go.
            alchemy_store.activities._update(activity)
        assert excinfo.value.args[0].startswith("The database already contains that")

    def test_update_with_invalid_pk(self, alchemy_store, activity, alchemy_activity):
        """Make sure that calling update without a PK raises exception."""
        activity.pk = alchemy_activity.pk + 1
        with pytest.raises(KeyError) as excinfo:
            alchemy_store.activities._update(activity)
        assert excinfo.value.args[0].startswith("No Activity with PK")

    def test_update_with_existing_category(
        self,
        alchemy_store,
        alchemy_activity,
        alchemy_category_factory,
    ):
        """
        Test that updateting an activity with existing category does not
        create a new one.
        """
        activity = alchemy_activity.as_hamster(alchemy_store)
        category = alchemy_category_factory().as_hamster(alchemy_store)
        assert alchemy_activity.category != category
        activity.category = category
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 2
        result = alchemy_store.activities._update(activity)
        db_instance = alchemy_store.session.query(AlchemyActivity).get(result.pk)
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        assert alchemy_store.session.query(AlchemyCategory).count() == 2
        assert db_instance.as_hamster(alchemy_store).equal_fields(activity)

    def test_update_name(
        self,
        alchemy_store,
        alchemy_activity,
        name_string_valid_parametrized,
    ):
        """Test updateing an activities name with a valid new string."""
        activity = alchemy_activity.as_hamster(alchemy_store)
        activity.name = name_string_valid_parametrized
        result = alchemy_store.activities._update(activity)
        db_instance = alchemy_store.session.query(AlchemyActivity).get(result.pk)
        assert db_instance.as_hamster(alchemy_store).equal_fields(activity)

    # ***

    def test_remove_existing(self, alchemy_store, alchemy_activity):
        """Make sure removing an existsing alchemy_activity works as intended."""
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        activity = alchemy_activity.as_hamster(alchemy_store)
        alchemy_store.activities.remove(activity)
        assert alchemy_store.session.query(AlchemyActivity).count() == 0

    def test_remove_no_pk(self, alchemy_store, activity):
        """
        Make sure that trying to remove an alchemy_activity without a PK
        raises error.
        """
        with pytest.raises(ValueError):
            alchemy_store.activities.remove(activity)

    def test_remove_invalid_pk(self, alchemy_store, alchemy_activity):
        """Test that removing of a non-existent key raises error."""
        assert alchemy_store.session.query(AlchemyActivity).count() == 1
        activity = alchemy_activity.as_hamster(alchemy_store)
        activity.pk = activity.pk + 1
        with pytest.raises(KeyError):
            alchemy_store.activities.remove(activity)
        assert alchemy_store.session.query(AlchemyActivity).count() == 1

    def test_get_existing(self, alchemy_store, alchemy_activity):
        """
        Make sure that retrieving an existing alchemy_activity by pk works
        as intended.
        """
        result = alchemy_store.activities.get(alchemy_activity.pk)
        assert result == alchemy_activity.as_hamster(alchemy_store)
        assert result is not alchemy_activity

    def test_get_existing_raw(self, alchemy_store, alchemy_activity):
        """
        Make sure that retrieving an existing alchemy_activity by pk works
        as intended.
        """
        result = alchemy_store.activities.get(alchemy_activity.pk, raw=True)
        assert result == alchemy_activity
        assert result is alchemy_activity

    # FIXME: Add deleted/hidden tests...
    # FIXME: Split this file into one file for each item type.
    def test_get_existing_deleted_false(self, alchemy_store, alchemy_activity):
        """
        Make sure that retrieving an existing alchemy_activity by
        deleted=False works as intended.
        """
        result = alchemy_store.activities.get(alchemy_activity.pk, deleted=False)
        assert result == alchemy_activity.as_hamster(alchemy_store)
        assert result is not alchemy_activity

    def test_get_existing_deleted_true(self, alchemy_store, alchemy_activity_deleted):
        """
        Make sure that retrieving an existing alchemy_activity by
        deleted=True works as intended.
        """
        result = alchemy_store.activities.get(alchemy_activity_deleted.pk, deleted=True)
        assert result == alchemy_activity_deleted.as_hamster(alchemy_store)
        assert result is not alchemy_activity_deleted

    def test_get_non_existing(self, alchemy_store):
        """Make sure quering for a non existent PK raises error."""
        with pytest.raises(KeyError):
            alchemy_store.activities.get(4)

    @pytest.mark.parametrize("raw", (True, False))
    def test_get_by_composite_valid(self, alchemy_store, alchemy_activity, raw):
        """Make sure that querying for a valid name/alchemy_category combo succeeds."""
        activity = alchemy_activity.as_hamster(alchemy_store)
        result = alchemy_store.activities.get_by_composite(
            activity.name,
            activity.category,
            raw=raw,
        )
        if raw:
            assert result == alchemy_activity
            assert result is alchemy_activity
        else:
            assert result == alchemy_activity
            assert result is not alchemy_activity

    def test_get_by_composite_invalid_category(
        self,
        alchemy_store,
        alchemy_activity,
        alchemy_category_factory,
    ):
        """Make sure that querying with an invalid category raises errror."""
        activity = alchemy_activity.as_hamster(alchemy_store)
        category = alchemy_category_factory().as_hamster(alchemy_store)
        with pytest.raises(KeyError):
            alchemy_store.activities.get_by_composite(activity.name, category)

    def test_get_by_composite_invalid_name(
        self,
        alchemy_store,
        alchemy_activity,
        name_string_valid_parametrized,
    ):
        """Make sure that querying with an invalid alchemy_category raises errror."""
        activity = alchemy_activity.as_hamster(alchemy_store)
        invalid_name = activity.name + "foobar"
        with pytest.raises(KeyError):
            alchemy_store.activities.get_by_composite(invalid_name, activity.category)

    def test_get_all_without_category(self, alchemy_store, alchemy_activity):
        """Make sure method returns all activities."""
        results = alchemy_store.activities.get_all()
        assert len(results) == 1

    def test_get_all_with_category_none(
        self,
        alchemy_store,
        alchemy_activity,
        alchemy_activity_factory,
    ):
        """Make sure only activity without a category is returned."""
        activity_without_category = alchemy_activity_factory(category=None)
        results = alchemy_store.activities.get_all(match_categories=[None])
        assert len(results) == 1
        assert results[0] == activity_without_category

    def test_get_all_with_category_named(
        self,
        alchemy_store,
        alchemy_activity,
        alchemy_activity_factory,
    ):
        """Make sure only activity matching the given alchemy_category is returned."""
        # Add Activity without Category to data store.
        # F841 local variable 'foo' is assigned to but never used
        _activity_sans_category = alchemy_activity_factory(category=None)  # noqa: F841
        results = alchemy_store.activities.get_all(
            match_categories=[alchemy_activity.category],
        )
        assert len(results) == 1
        assert results[0] == alchemy_activity

    def test_get_all_with_category_both_none_and_named(
        self,
        alchemy_store,
        alchemy_activity,
        alchemy_activity_factory,
    ):
        """Make sure both activities with category name and with none are returned."""
        # Add Activity without Category to data store.
        _activity_sans_category = alchemy_activity_factory(category=None)  # noqa: F841
        results = alchemy_store.activities.get_all(
            match_categories=[None, alchemy_activity.category],
        )
        assert len(results) == 2

    def test_get_all_with_search_term(self, alchemy_store, alchemy_activity):
        """
        Make sure that activities matching the given term ass name are returned.
        """
        # (lb): This test previously hydrated the AlchemyActivity into a proper
        # Activity, but it passes fine without. So not sure if I'm missing
        # something, but we can skip this step:
        #   activity = alchemy_activity.as_hamster(alchemy_store)
        # (and could probably do the same elsewhere in this file, but not
        # really worth the time -- just something I wanted to note).
        results = alchemy_store.activities.get_all(
            match_categories=[alchemy_activity.category],
            search_terms=[alchemy_activity.name],
        )
        assert len(results) == 1

    def test_get_all_with_category_miss(self, alchemy_store, alchemy_activity):
        """
        Make sure that activities matching the given alchemy_category are returned.
        """
        results = alchemy_store.activities.get_all(match_categories=["miss"])
        assert len(results) == 0
        assert alchemy_activity == alchemy_store.activities.get_all()[0]

    def test_get_deleted_item(self, alchemy_store, alchemy_activity):
        """Make sure method retrieves deleted object."""
        alchemy_activity.deleted = True
        result = alchemy_store.activities.get(alchemy_activity.pk, deleted=True)
        assert result == alchemy_activity

    def test_get_all_match_activities(
        self,
        alchemy_store,
        set_of_alchemy_facts_active,
        alchemy_activity_factory,
    ):
        """Test get_all argument: QueryTerms.match_activities."""
        # Cover as many branches as possible within query_filter_by_activity
        # and query_filter_by_activity_name.
        activity_0 = set_of_alchemy_facts_active[0].activity
        activity_2 = set_of_alchemy_facts_active[2].activity.name
        # Rather than use alchemy_activity or alchemy_activity_factory,
        # which will insist that PK by non-None (though possibly 0 is okay,
        # and we could test the same path...), use a normal Activity.
        # This will assign a new PK:
        any_activity = alchemy_activity_factory(pk=None)
        activity_with_pk_None = Activity(name=any_activity.name)
        results = alchemy_store.activities.get_all(
            match_activities=[
                activity_0,
                activity_2,
                activity_with_pk_None,
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
        alchemy_store.activities.get_all(sort_cols=sort_cols)

    def test_get_all_sort_cols_tag_fails(self, alchemy_store, mocker):
        # The tag table is not joined for Activity query.
        mocker.patch.object(alchemy_store.logger, "warning")
        alchemy_store.activities.get_all(sort_cols=["tag"])
        assert alchemy_store.logger.warning.called

    def test_get_all_sort_cols_unknown(self, alchemy_store, mocker):
        mocker.patch.object(alchemy_store.logger, "warning")
        alchemy_store.activities.get_all(sort_cols=["foo"])
        assert alchemy_store.logger.warning.called
