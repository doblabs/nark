# This file exists within 'nark':
#
#   https://github.com/hotoffthehamster/nark

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
    # "Very simple Python library for color and formatting in terminal."
    # Forked (for italic "support") to:
    #  https://github.com/hotoffthehamster/ansi-escape-room
    # Forked from:
    #  https://gitlab.com/dslackw/colored
    # See wrapper file:
    #  nark/helpers/emphasis.py
    'ansi-escape-room',
    # Platform-specific directory magic.
    #  https://github.com/ActiveState/appdirs
    'appdirs',
    # Pythonic config @decorator.
    #  https://github.com/hotoffthehamster/config-decorator
    'config_decorator >= 0.4.0',
    # Better INI/conf parser (preserves order, comments) than ConfigParser.
    #  https://github.com/DiffSK/configobj
    #  https://configobj.readthedocs.io/en/latest/
    'configobj >= 5.0.6',
    # https://github.com/scrapinghub/dateparser
    'dateparser',
    # Elapsed timedelta formatter, e.g., "1.25 days".
    'human-friendly_pedantic-timedelta >= 0.0.6',  # Imports as pedantic_timedelta.
    # https://github.com/collective/icalendar
    'icalendar',
    # https://bitbucket.org/micktwomey/pyiso8601
    'iso8601',
    # https://github.com/mnmelo/lazy_import
    'lazy_import',
    # Daylight saving time-aware timezone library.
    #  https://pythonhosted.org/pytz/
    'pytz',
    # For testing with dateparser,
    #   https://bitbucket.org/mrabarnett/mrab-regex
    #   https://pypi.org/project/regex/
    # FIXME/2019-02-19 18:13: Latest regex is broken.
    #   https://pypi.org/project/regex/2019.02.20/
    #   https://bitbucket.org/mrabarnett/mrab-regex/commits/
    #       5d8b8bb2b64b696cdbaa7bdc0dce4b462d311134#Lregex_3/regex.pyF400
    # Because of recent change to import line (was made self-referential):
    #      .tox/py37/lib/python3.7/site-packages/regex.py:400: in <module>
    #          import regex._regex_core as _regex_core
    #      E   ModuleNotFoundError: No module named 'regex._regex_core';
    #       'regex' is not a package
    'regex == 2019.02.18',
    # https://www.sqlalchemy.org/
    # MAYBE/2019-11-02: (lb): Migrate to SQLalchemy 1.3. Until then, stuck on 1.2.
    # 'sqlalchemy',
    'sqlalchemy >= 1.2.19, < 1.3',
    # Database gooser/versioner.
    #  https://pypi.org/project/sqlalchemy-migrate/
    #  https://sqlalchemy-migrate.readthedocs.io/en/latest/
    # 2019-02-21: (lb): Forked again! Package alt. that accepts static config.
    'sqlalchemy-migrate-dob >= 0.12.1',
    # https://github.com/regebro/tzlocal
    'tzlocal',
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
    #     ['release_ghub_pypi', 'tests', 'tests.release_ghub_pypi']
    # - With the 'exclude*' rule, this call is essentially:
    #     packages=['release_ghub_pypi']
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

