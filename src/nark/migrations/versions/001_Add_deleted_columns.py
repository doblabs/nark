# This file exists within 'nark':
#
#   https://github.com/tallybark/nark
#
# Copyright © 2018-2020 Landon Bouma
# All rights reserved.
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

from sqlalchemy import Column, ForeignKey, Integer, MetaData, Table

# USAGE: You could run this script manually, invoking SQLAlchemy-migrate, e.g.,
#
#           py3 migrations/manage.py upgrade <db_url> migrations
#
#       Or you could-should run it with the hamster CLI, dob.
#
#           dob migrate up

# NOTE: This script will work against the Legacy Hamster DB on upgrade,
#       but on downgrade, it'll barf an sqlite3.IntegrityError.
#
#       So be sure you upgrade your legacy Hamster database:
#
#           dob store upgrade-legacy ~/.local/share/hamster-applet/hamster.db

# NOTE! We cannot use sqlalchemy.Boolean, lest downgrade barfs!
#
# E.g.,
#
#
#       def upgrade(migrate_engine):
#           ...
#           deleted_c = Column('deleted', Boolean)
#
#       def downgrade(migrate_engine):
#           ...
#           activities.c.deleted.drop()
#
#       $ py3 migrations/manage.py test ${db_url} migrations
#       Upgrading...
#       done
#       Downgrading...
#
#       sqlite3.OperationalError: no such column: deleted
#
#       ...
#
#       sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such column:
#       deleted [SQL: '\nCREATE TABLE categories (\n\tid INTEGER NOT NULL,
#                      \n\tname TEXT(500), \n\tcolor_code TEXT(50),
#                      \n\tcategory_order INTEGER, \n\tsearch_name TEXT,
#                      \n\tPRIMARY KEY (id), \n\tCHECK (deleted IN (0, 1))\n)\n\n']
#       (Background on this error at: http://sqlalche.me/e/e3q8)


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    activities = Table('activities', meta, autoload=True)
    categories = Table('categories', meta, autoload=True)
    tags = Table('tags', meta, autoload=True)
    facts = Table('facts', meta, autoload=True)

    # SKIP: Activity.deleted already exists.
    upgrade_add_column_boolean(categories, 'deleted')
    upgrade_add_column_boolean(tags, 'deleted')
    upgrade_add_column_boolean(facts, 'deleted')

    # Make a column to store the split-from ID, for edited/split facts.
    # MAYBE: index=True ??
    split_from_id = Column(
        'split_from_id', Integer, ForeignKey(facts.c.id), nullable=True,
    )
    split_from_id.create(facts)

    upgrade_add_column_boolean(activities, 'hidden')
    upgrade_add_column_boolean(categories, 'hidden')
    upgrade_add_column_boolean(tags, 'hidden')
    # SKIP: Facts.hidden probably does not compute.
    #       (Hidden is for auto-complete/MRU lists.)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    activities = Table('activities', meta, autoload=True)
    categories = Table('categories', meta, autoload=True)
    tags = Table('tags', meta, autoload=True)
    facts = Table('facts', meta, autoload=True)

    facts.c.split_from_id.drop()

    facts.c.deleted.drop()
    tags.c.deleted.drop()
    categories.c.deleted.drop()

    # SKIP: facts.c.hidden.drop()
    tags.c.hidden.drop()
    categories.c.hidden.drop()
    activities.c.hidden.drop()


def upgrade_add_column_boolean(table, column):
    # NOTE: (lb): SQLite3 is weird. It preserves the whitespace of
    #       your CREATE TABLE, I think, because after adding the two
    #       columns, deleted and hidden, they're just appended to the
    #       last column's line in the .schema, e.g.,:
    #           sqlite> .schema categories
    #
    #           CREATE TABLE categories (
    #           	id INTEGER NOT NULL,
    #           	name VARCHAR(254), deleted INTEGER, hidden INTEGER,
    #           	PRIMARY KEY (id),
    #           	UNIQUE (name)
    #           );
    #
    # HUH: (lb): Furthermore, SQLAlchemy-migrate preserves whitespace on
    #      upgrade, but now on downgrade.
    #
    #      E.g., support you define you table without newlines, e.g.,:
    #
    #           CREATE TABLE categories (
    #               id INTEGER NOT NULL,
    #               name VARCHAR(254),
    #               PRIMARY KEY (id),
    #               UNIQUE (name)
    #           );
    #
    #      And then you run this script to upgrade. You'll see:
    #
    #           CREATE TABLE categories (
    #               id INTEGER NOT NULL,
    #               name VARCHAR(254),
    #               deleted INTEGER,
    #               hidden INTEGER,
    #               PRIMARY KEY (id),
    #               UNIQUE (name)
    #           );
    #
    #      Then you run this script to downgrade. You'll now see newlines!
    #
    #           CREATE TABLE categories (
    #           	id INTEGER NOT NULL,
    #           	name VARCHAR(254),
    #           	PRIMARY KEY (id),
    #           	UNIQUE (name)
    #           );
    #
    #      Not that any of this matters. It's just interesting.

    # NOTE: We cannot set ``nullable=False`` because existing rows
    #       will violate the constraint. But we can do it soon enough.
    deleted_c = Column(column, Integer, default=False)

    deleted_c.create(table)

    # Get rid of the DEFAULT=FALSE (used to set the cell values)
    # and set NOT NULL.
    deleted_c.alter(nullable=False)

