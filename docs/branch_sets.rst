Branch Sets
===========

*Branch Sets* is a concept introduced by ``clue`` to simplify the process of working
with multiple repositories during feature development.

Some of the ``clue git`` subcommands only apply to branch sets, some have additional
capabilities when operating on branch sets.

Branch sets are configured in the ``branches.yaml`` file that was generated when
``clue env create`` was first run in ``clue``'s work dir.

.. note::
    Making modifications to the ``branches.yaml`` file, does not require
    running ``clue apply`` for them to take place. Making modifications
    to the active branch set, does however require that you ``clue git checkout``
    the branch set again, for the changes to take places. (explanations follow)

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

.. _base_branch:

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

Active Branch Set Git Related Commands
--------------------------------------
Now that we know about this *active branch set* concept, what does it actually
give us, except for easily switching between sets of branches?

Well, it gives some convenience, but not much more. Are you excited yet?

``clue git status --active``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
After ``clue git checkout {{branch_set_name}}``, ``branch_set_name`` is the
*active branch set*. If you want to see the status only for repositories that
are part of the active branch set, you can can pass the ``--active/-a`` flag
to the status command

.. code-block:: sh

    $ clue git status -a

``clue git reset``
^^^^^^^^^^^^^^^^^^
If you wish to reset all changes made to repositories in the active branch set
to their origin branch state, run:

.. code-block:: sh

    $ clue git reset

To do a hard reset, pass ``--hard/-h``. To reset from a different origin than
the default ``origin``, pass ``--origin=MY_REMOTE``.

``clue git squash``
^^^^^^^^^^^^^^^^^^^
If you wish to squash all commits for each branch in the active branch set, run:

.. code-block:: sh

    $ clue git squash

For each repository, ``clue`` will squash all commits that come after the branch
set ``base`` (``master`` by default, see :ref:`base_branch`), to a single commit. (If there is only one
commit already, no action will take place for that repository).

.. warning::
    For any branch whose state before the squash was already pushed to origin,
    a subsequent ``git push -f`` will be required. Use with care, and certainly
    never use this on branches for which you are not the only active developer.

``clue git rebase``
^^^^^^^^^^^^^^^^^^^
A complementary command to the previous ``clue git squash`` is the ``rebase``
command, which will, as its name implies, rebase each branch in the active branch
set, on top of the branch set ``base``.

.. code-block:: sh

    $ clue git rebase

If a clean rebase cannot be performed,
the rebase for that branch will be aborted. You will usually run this command
after running ``clue git squash`` when your prepare your branches for a pull
request.

.. warning::
    For any branch whose state before the rebase was already pushed to origin,
    a subsequent ``git push -f`` will be required. Use with care, and certainly
    never use this on branches for which you are not the only active developer.


``clue branch``
^^^^^^^^^^^^^^^
The ``clue branch`` command will give you a quick look of what you have
configured in your ``branches.yaml`` file. It will also indicate the
currently active branch set with a red * to the left of the branch set name
(if there is one).

For example (the actual output is nicely colored):

.. code-block:: sh

    $ clue branch
      delete-logs:
        branch: CFY-4864-delete-deployment-logs
        repos:
        - cloudify-manager

      testing:
        repos:
          cloudify-agent: CFY-12312-agent-fixes
          cloudify-plugins-common: CFY-12312-common-fixes

      lifecycle:
        branch: CFY-4470-extendable-lifecycle
        base: 3.4m2-build
        repos:
        - cloudify-manager
        - cloudify-plugins-common

    * plugins:
        branch: CFY-4863-install-plugins
        repos:
        - cloudify-manager
        - cloudify-agent
