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

"""Raw SQLite3 commands to upgrade legacy hamster-applet database."""

from gettext import gettext as _

import logging
import sqlite3

logger = logging.getLogger('nark.log')


# (lb): Because SQLite3 does not support ALTER TABLE ... DROP COLUMN,
# we instead rename all tables, recreate new tables with old names,
# and then shuffle everything over. Enjoy!

def upgrade_legacy_db_hamster_applet(db_path):
    """"""
    def _upgrade_legacy_db_hamster_applet():
        # The caller will have copied the legacy db to db_path.
        conn, curs = begin_transaction()
        verify_legacy_version(curs)
        rename_old_tables(curs)
        create_new_tables(curs)
        populate_tables(curs)
        drop_old_tables(curs)
        commit_transaction(conn)

    def begin_transaction():
        # (lb): sqlite3 commits automatically. Tell it not to.
        conn = sqlite3.connect(db_path, isolation_level=None)
        curs = conn.cursor()
        # (lb): Not sure BEGIN TRANSACTION does anything, because isolation_level.
        curs.execute('BEGIN TRANSACTION')
        return conn, curs

    def commit_transaction(conn):
        conn.commit()
        conn.close()

    def verify_legacy_version(curs):
        curs.execute('SELECT * FROM version')
        versions = curs.fetchall()
        if len(versions) > 1:
            raise Exception(_(
                'Found more than 1 version entry: {}'
            ).format(versions))
        elif not len(versions):
            raise Exception(_('That database has no version entry.'))
        else:
            db_version = versions[0][0]
            logger.debug('Legacy DB Version: {}'.format(db_version))
            if db_version != 9:
                raise Exception(_(
                    "ERROR: Expected Legacy DB Version “9”, but found: {}"
                ).format(db_version))

    table_names = ['activities', 'categories', 'tags', 'facts', 'fact_tags']

    def rename_old_tables(curs):
        for table in table_names:
            curs.execute(
                'ALTER TABLE {table} RENAME TO temp_{table}'
                .format(table=table)
            )

    def create_new_tables(curs):
        """"""
        # NOTE: (lb): To form the CREATE TABLE statements, I simply ran
        #  ``.schema`` against a new DB created by ``dob store create``.
        create_categories(curs)
        create_facts(curs)
        create_fact_tags(curs)
        create_tags(curs)
        create_activities(curs)

    def create_categories(curs):
        # NOTE: (lb): Not recreating these legacy columns from categories:
        #   color_code varchar2(50)  # empty ((lb): at least in my legacy db)
        #   category_order integer   # empty ((lb): at least in my legacy db)
        #   search_name varchar2     # simply, name.lower()
        curs.execute(
            '''
            CREATE TABLE categories (
                id INTEGER NOT NULL,
                name VARCHAR(254),
                PRIMARY KEY (id),
                UNIQUE (name)
            )
            '''
        )

    def create_activities(curs):
        # NOTE: (lb): Not recreating these legacy columns from activities:
        #   work integer            # empty ((lb): at least in my legacy db)
        #   activity_order integer  # empty ((lb): at least in my legacy db)
        #   search_name varchar2    # simply, name.lower()
        curs.execute(
            '''
            CREATE TABLE activities (
                id INTEGER NOT NULL,
                name VARCHAR(500),
                deleted BOOLEAN,
                category_id INTEGER,
                PRIMARY KEY (id),
                UNIQUE (name, category_id),
                CHECK (deleted IN (0, 1)),
                FOREIGN KEY(category_id) REFERENCES categories (id)
            )
            '''
        )

    def create_tags(curs):
        # NOTE: (lb): Not recreating these legacy columns from tags:
        #   autocomplete BOOL DEFAULT true
        #   # (lb): I think autocomplete was the list that the legacy
        #   # ``hamster-indicator`` app let you edit in the interface.
        #   # This option is reimplemented using new ``hidden`` columns.
        curs.execute(
            '''
            CREATE TABLE tags (
                id INTEGER NOT NULL,
                name VARCHAR(254),
                PRIMARY KEY (id),
                UNIQUE (name)
            )
            '''
        )

    def create_facts(curs):
        curs.execute(
            '''
            CREATE TABLE facts (
                id INTEGER NOT NULL,
                start_time DATETIME,
                end_time DATETIME,
                activity_id INTEGER,
                description VARCHAR(500),
                PRIMARY KEY (id),
                FOREIGN KEY(activity_id) REFERENCES activities (id)
            )
            '''
        )

    def create_fact_tags(curs):
        curs.execute(
            '''
            CREATE TABLE fact_tags (
                fact_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY(fact_id) REFERENCES facts (id),
                FOREIGN KEY(tag_id) REFERENCES tags (id)
            )
            '''
        )

    def populate_tables(curs):
        populate_activities(curs)
        populate_categories(curs)
        populate_tags(curs)
        populate_facts(curs)
        populate_fact_tags(curs)

    def populate_activities(curs):
        curs.execute(
            '''
            INSERT INTO activities
            SELECT
                id, name, deleted, category_id
            FROM
                temp_activities
            '''
        )

    def populate_categories(curs):
        curs.execute(
            '''
            INSERT INTO categories
            SELECT
                id, name
            FROM
                temp_categories
            '''
        )

    def populate_tags(curs):
        curs.execute(
            '''
            INSERT INTO tags
            SELECT
                id, name
            FROM
                temp_tags
            '''
        )

    def populate_facts(curs):
        curs.execute(
            '''
            INSERT INTO facts
            SELECT
                id, start_time, end_time, activity_id, description
            FROM
                temp_facts
            '''
        )

    def populate_fact_tags(curs):
        curs.execute(
            '''
            INSERT INTO fact_tags
            SELECT
                fact_id, tag_id
            FROM
                temp_fact_tags
            '''
        )

    def drop_old_tables(curs):
        drop_tmp_tables(curs)
        drop_legacy_goo(curs)

    def drop_tmp_tables(curs):
        for table in reversed(table_names):
            curs.execute(
                'DROP TABLE temp_{table}'
                .format(table=table)
            )

    def drop_legacy_goo(curs):
        # Other legacy stuff to drop.
        drop_table_version(curs)

    def drop_table_version(curs):
        # (lb): Had one row, with one cell (version integer), set to "9".
        #   CREATE TABLE version(version integer);
        curs.execute('DROP TABLE version')

    def drop_old_fact_index(curs):
        # (lb): I think this virtual table was for some sort of search feature.
        #   It runs functions.
        #
        # From hamster-applet/src/hamster/db.py:
        #
        #   def run_fixtures(self):
        #       ...
        #       if version < 9:
        #           # adding full text search
        #           self.execute("""
        #               CREATE VIRTUAL TABLE fact_index
        #               USING fts3(id, name, category, description, tag)""")
        #
        # See:
        #
        #   https://www.sqlite.org/fts3.html
        #
        # NOTE: Dropping fact_index automatically drops three related tables:
        #
        #   fact_index_content
        #   fact_index_segments
        #   fact_index_segdir
        #
        curs.execute('DROP TABLE fact_index')

    _upgrade_legacy_db_hamster_applet()

