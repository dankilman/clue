Installation
============

Prerequisites
-------------
`virtualenvwrapper <http://virtualenvwrapper.readthedocs.org/en/latest/install.html>`_
should be installed and configured in your environment.

Installing The Code
-------------------

Create a dedicated virtualenv for ``clue`` and install ``clue`` in that environment.
This is important because we don't want ``clue``'s dependencies interfering
with python dependencies that are part of your development environment:

.. code-block:: sh

    $ mkvirtualenv clue
    $ pip install clue


.. note::
    While ``clue`` is installed in its own virtualenv, you won't generally need
    to ``workon clue`` when working with it, because the virtualenv that is
    managed by ``clue`` will have a symlink to ``clue`` in its ``bin`` directory.

Setting Up The Environment
--------------------------
#. Choose a location that will serve as the work directory for ``clue``.
   For example:

    .. code-block:: sh

        $ export CLUE_HOME=$HOME/clue
        $ mkdir -p CLUE_HOME

#. Create a ``clue`` environment in the work directory.
   You should choose a location that will serve as the root dir for GitHub
   repositories managed by ``clue`` (``--repos-dir``). Note that you can point
   to an existing directory that already contains some repositories, so that
   they can be managed by ``clue``.

    .. code-block:: sh

        $ cd $CLUE_HOME
        $ clue env create --repos-dir=$HOME/dev/repos

The ``env create`` command created three files: ``inputs.yaml``, ``branches.yaml``
and ``macros.yaml`` which are covered in their own sections.

It also created (or updated) a global configuration file located at ``~/.clue``
which points to your workdir. This enables you to run ``clue`` commands on your
development environment, regardless of your ``$PWD``.

It will make sense to have the work directory managed by ``git`` locally.

The next sections go into details showing how ``clue`` may be useful in
simplifying your day to day interactions with your development environment.
