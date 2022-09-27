# This file exists within 'nark':
#
#   https://github.com/tallybark/nark

"""
Packaging instruction for setup tools.

Refs:

  https://setuptools.readthedocs.io/

  https://packaging.python.org/en/latest/distributing.html

  https://github.com/pypa/sampleproject
"""

from setuptools import find_packages, setup

# *** Package requirements.

requirements = [
    # Better INI/conf parser (preserves order, comments) than ConfigParser.
    #  https://github.com/DiffSK/configobj
    #  https://configobj.readthedocs.io/en/latest/
    'configobj >= 5.0.6, < 6',
    # https://github.com/scrapinghub/dateparser
    'dateparser >= 0.7.4, < 1',
    # https://github.com/collective/icalendar
    'icalendar >= 4.0.5, < 5',
    # https://bitbucket.org/micktwomey/pyiso8601
    'iso8601 >= 0.1.12, < 1',
    # https://github.com/mnmelo/lazy_import
    'lazy_import >= 0.2.2, < 1',
    # Daylight saving time-aware timezone library.
    #  https://pythonhosted.org/pytz/
    'pytz >= 2019.3',
    # https://www.sqlalchemy.org/
    'sqlalchemy >= 1.3.16, < 1.4',
    # https://github.com/regebro/tzlocal
    'tzlocal >= 2.0.0, < 3',

    # *** HOTH packages.

    # "Very simple Python library for color and formatting in terminal."
    # Forked by HOTH (for italic "support"):
    #  https://github.com/hotoffthehamster/ansi-escape-room
    # Forked from dslackw:
    #  https://gitlab.com/dslackw/colored
    # Used in nark to format log messages, but also installed by dob(-bright),
    #  so not really adding any overhead.
    'ansi-escape-room == 1.4.2',
    # "textwrap, but savvy to ANSI colors"
    #  https://github.com/jonathaneunice/ansiwrap
    # Forked to update to latest Pythons
    #  https://github.com/hotoffthehamster/ansiwrap
    'ansiwrap-hotoffthehamster == 0.8.4',
    # Pythonic config @decorator.
    #  https://github.com/hotoffthehamster/config-decorator
    'config-decorator > 2.0.14, < 2.0.16',  # I.e., release 2.0.15 or dev vers from that.
    # ActiveState/appdirs + Singleton (app-wide access w/out appname) + `mkdir -p`.
    #  https://github.com/doblabs/easy-as-pypi-appdirs#🛣
    'easy-as-pypi-appdirs',
    # Get-package-or-Git-version helper.
    #  https://github.com/hotoffthehamster/easy-as-pypi-getver
    'easy-as-pypi-getver',
    # Elapsed timedelta formatter, e.g., "1.25 days".
    # - Imports as `pedantic_timedelta`.
    #  https://github.com/hotoffthehamster/human-friendly_pedantic-timedelta
    'human-friendly_pedantic-timedelta > 2.0.11, < 2.0.13',
    # Database gooser/versioner.
    #  https://pypi.org/project/sqlalchemy-migrate/
    #  https://sqlalchemy-migrate.readthedocs.io/en/latest/
    # 2019-02-21: (lb): Forked again! Package alt. that accepts static config.
    'sqlalchemy-migrate-hotoffthehamster == 0.13.0',
]

# *** Minimal setup() function -- Prefer using config where possible.

# (lb): Most settings are in setup.cfg, except identifying packages.
# (We could find-packages from within setup.cfg, but it's convoluted.)

setup(
    # Run-time dependencies installed on `pip install`. To learn more
    # about "install_requires" vs pip's requirements files, see:
    #   https://packaging.python.org/en/latest/requirements.html
    install_requires=requirements,

    # Specify which package(s) to install.
    # - Without any rules, find_packages returns, e.g.,
    #     ['nark', 'tests', 'tests.nark']
    # - With the 'exclude*' rule, this call is essentially:
    #     packages=['nark']
    packages=find_packages(exclude=['tests*']),

    # Tell setuptools to determine the version
    # from the latest SCM (git) version tag.
    #
    # Note that if the latest commit is not tagged with a version,
    # or if your working tree or index is dirty, then the version
    # from git will be appended with the commit hash that has the
    # version tag, as well as some sort of 'distance' identifier.
    # E.g., if a project has a '3.0.0a21' version tag but it's not
    # on HEAD, or if the tree or index is dirty, the version might
    # be:
    #   $ python setup.py --version
    #   3.0.0a22.dev3+g6f93d8c.d20190221
    # But if you clean up your working directory and move the tag
    # to the latest commit, you'll get the plain version, e.g.,
    #   $ python setup.py --version
    #   3.0.0a31
    # Ref:
    #   https://github.com/pypa/setuptools_scm
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
)

