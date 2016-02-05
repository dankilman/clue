Branch Sets
===========

*Branch Sets* is a concept introduced by ``clue`` to simplify to process of working
with multiple repositories during feature development.

Some of the ``clue git`` subcommands only apply to branch sets, some have additional
capabilities when operating on branch sets.

Branch sets are configured in the ``branches.yaml`` file that was generated when
``clue env create`` was first run in ``clue``'s work dir.

.. note::
    Making modifications to the ``branches.yaml`` file, does not require
    running ``clue apply`` for them to take place. Making modifications
    to the active branch set, does however require that you ``clue git checkout``
    the branch set, again for the changes to take places. (explanations follow)

Basic Usage
-----------

The ``branches.yaml`` file is a simple dictionary that maps from branch set
names to branch set definitions.

.. code-block:: yaml

    my_first_feature:
      branch: CFY-10101-my-first-feature
      repos:
      - cloudify-rest-client
      - cloudify-plugins-common

In the previous example, we configured a single branch set named ``my_first_feature``.
The repositories involved in this feature are ``cloudify-rest-client`` and
``cloudify-plugins-common``.
The branch for all repositories in this case is ``CFY-10101-my-first-feature``

To *activate* the branch set, run:

.. code-block:: sh

    $ clue git checkout my_first_feature

.. tip::
    Bash completion is available for branch set names.

After running the ``clue git checkout`` command, the ``my_first_feature`` branch
set is considered by ``clue`` to be the *active branch set*.
What actually happens when this command is executed is that
``cloudify-rest-client`` and ``cloudify-plugins-common``, ``CFY-10101-my-first-feature``
branch is checked out. For all other repositories, the default branch is checked out.
(by default, this branch is ``master``)

Different Branches
------------------
If your feature involves different repositories with different branches for each
repository, you can omit the ``branch`` property and pass a dictionary to the
``repos`` property where each entry maps from a repo name to its matching branch.

.. code-block:: yaml

    my_second_feature:
      repos:
        cloudify-rest-client: CFY-10102-rest-modifications
        cloudify-plugins-common: CFY-10102-new-api

Base Branch
-----------
By default, all branches are assumed to be based out of the ``master`` branch.
How this is used is explained in the following sections, but for now, know that
you can override the base branch by specifying the ``base`` property.

.. code-block:: yaml

    my_second_feature_backport:
      base: 3.4m1-build
      repos:
        cloudify-rest-client: CFY-10102-rest-modifications-m1
        cloudify-plugins-common: CFY-10102-new-api-m1
