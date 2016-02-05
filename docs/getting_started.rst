Getting Started
===============

Basic Usage
-----------

The ``inputs.yaml`` in ``clue``'s workdir, contains configuration for most
aspects of environments managed by ``clue``.

Before you can start using ``clue`` you may need/want to make some modifications
to the inputs file. Most inputs already have sane defaults for managing a Cloudify
based environment. In this section, we'll go over the different inputs.

``branches_file``
^^^^^^^^^^^^^^^^^
The ``branches_file`` input points to the location of the ``branches.yaml`` used
by ``clue``. The default value already point to a file that was generated during
environment creation. You can leave the default value as is for now. When we
talk about *Active Branch Sets*, we'll get back to this file.

``clone_method``
^^^^^^^^^^^^^^^^
By default, ``clone_method`` is set to ``http``. If you use ``ssh`` to clone GitHub
repositories, change this value to ``ssh``.

``constraints``
^^^^^^^^^^^^^^^
You can specify a set of constraints that will be passed to every ``pip install``
command that ``clue`` executes. A set of initial values if provided, but you
can change this value to your liking.

``git_config``
^^^^^^^^^^^^^^
You can specify a key/value pairs that will be set globally on each repo that
is managed by ``clue``, for example, if you have something like this in your inputs

.. code-block:: yaml

    git_config:
      user.name: Johnnie Walker
      user.email: johnnie@example.com

Then the following git command will be executed on all GitHub repositories managed
by ``clue``

.. code-block:: sh

    $ git config user.name "Johnnie Walker"
    $ git config user.mail "johnnie@example.com"

This can be useful if you wish to have different values in your global git config.

``git_prompt_paths``
^^^^^^^^^^^^^^^^^^^^
List of values for the location of the ``git-prompt.sh`` file that comes bundled
with git installations. The ``clue git status`` command, makes use of this file
to produce detailed reports. The default value contains a few locations that are
known to exist on different distributions.
If none of the paths are found, ``clue git status`` will fallback to displaying
the branch name alone.

``organization``
^^^^^^^^^^^^^^^^
The default GitHub organization from which GitHub repositories will be cloned.
The default value is ``cloudify-cosmo`` but you can modify this value if you
want to use ``clue`` to manage different development environments.

.. note::
    You can also override the organization for specific repositories. This will
    be explained in the ``repos`` input section.

``register_python_argcomplete``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Each value in this list will be registered by python argcomplete in the ``postactive``
script of the managed virtualenv. The default value includes ``cfy``, ``clue``
and ``claw``.

.. warning::
    ``clue`` makes use of ``virtualenvwrapper``'s ``postactivate`` script to
    implement this feature. As such, it will override any file that may exist
    there (if ``clue`` is used to manage an existing virtualenv or if this file
    was modified manually and ``clue apply`` was called at some point). This
    is something to be aware of in case you need this file for additional
    purposes. Currently, it is not possible to provide additional configuration
    for this file, but if there is need, such feature will be implemented. (by
    me or by you).

