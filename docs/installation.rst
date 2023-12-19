############
Installation
############

.. vim:tw=0:ts=3:sw=3:et:norl:nospell:ft=rst

.. |virtualenv| replace:: ``virtualenv``
.. _virtualenv: https://virtualenv.pypa.io/en/latest/

.. |workon| replace:: ``workon``
.. _workon: https://virtualenvwrapper.readthedocs.io/en/latest/command_ref.html?highlight=workon#workon

To install system-wide, run as superuser::

    $ pip3 install nark

To install user-local, simply run::

    $ pip3 install -U nark

To install within a |virtualenv|_, try::

    $ cd "$(mktemp -d)"

    $ python3 -m venv .venv

    $ . ./.venv/bin/activate

    (nark) $ pip install nark

To develop on the project, link to the source files instead::

    (nark) $ deactivate
    $ git clone git@github.com:doblabs/nark.git
    $ cd nark
    $ python3 -m venv nark
    $ . ./.venv/bin/activate
    (nark) $ make develop

After creating the virtual environment, it's easy to start
developing from a fresh terminal::

    $ cd nark
    $ . ./.venv/bin/activate
    (nark) $ ...

