Features
========

*Features* is a concept introduced by ``clue`` to simplify the process of working
with multiple repositories during feature development.

Some of the ``clue git`` subcommands only apply to features, some have additional
capabilities when operating on features.

Features are managed by clue in the ``features.yaml`` file that was generated when
``clue env create`` was first run in ``clue``'s work dir.

``clue feature create``
-----------------------
To begin using features, first, you need to create them. Running
``clue feature create {{feature_name}} --branch {{branch}}`` will create a
new feature ``feature_name``, with ``branch`` as its branch. For example:

.. code-block:: sh

    $ clue feature create my_first_feature --branch CFY-10101-my-feature

You can also supply the ``--base`` flag to set a base different than ``master``
for a feature.

After running ``clue feature create``, the feature definition is added to the
``features.yaml`` file. In addition, all repos that currently have a branch matching
the supplied branch, will be added to the feature's repos list. The feature will
be activated and ``clue feature checkout {{feature_name}}`` will be applied to
it. (``checkout`` is explained in the following sections)

``clue feature list``
---------------------
The ``clue feature list`` command will give you a quick at the current
features in your ``features.yaml`` file. It will also indicate the
currently active feature with a red * to the left of the feature name
(if there is one).

For example (the actual output is nicely colored):

.. code-block:: sh

    $ clue feature list
      delete-logs:
        branch: CFY-4864-delete-deployment-logs
        repos:
        - cloudify-manager

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

``clue feature add-repo``
-------------------------
Running ``clue feature add-repo {{repo_name}}`` will add the repository
to the feature definition. If this repository doesn't have a branch matching the
feature branch, one will be created locally. The branch will also be checked out.

.. tip::
    Bash completion is available for git repository names.

``clue feature remove-repo``
----------------------------
Running ``clue feature remove-repo {{repo_name}}`` will remove the repository
from the feature definition. The branch for this repository will also be deleted
using ``git branch -d``. If this branch has commits that are not pushed to the upstream,
the branch will not be deleted (and the feature will not be removed).
If you wish to remove the repo from feature and its branch anyway, pass
``--force`` to the command so that ``git branch -D`` will be used.

.. tip::
    Bash completion is available for the active feature git repository names.

``clue feature sync-repos``
---------------------------
Running ``clue feature sync-repos`` will scan all repositories that have the feature
branch and will update the feature definition to include them. This will also
remove stale repos that no longer have this branch.

``clue feature checkout``
-------------------------
Running ``clue feature checkout {{feature_name}}`` will *activate* the feature.
``clue`` will checkout the feature branch in the feature repositories.
It will also checkout the default branch for any repository that is not included
in the feature definition.

``clue feature deactivate``
---------------------------
Running ``clue feature deactivate`` will simply deactivate the currently active
feature.

``clue feature finish``
-----------------------
Running ``clue feature finish`` will run ``clue feature remove-repo`` for each
repository in the feature definition, it will then remove the feature definition
and deactivate it.

Active Feature Git Related Commands
-----------------------------------
Now that we know about this *active feature* concept, what does it actually
give us, except for easily switching between sets of branches?

Well, it gives some convenience, but not much more. Are you excited yet?

``clue git status --active``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
After ``clue feature checkout {{feature_name}}``, ``feature`` is the
*active feature*. If you want to see the status only for repositories that
are part of the active feature, you can can pass the ``--active/-a`` flag
to the status command

.. code-block:: sh

    $ clue git status -a

``clue git reset``
^^^^^^^^^^^^^^^^^^
If you wish to reset all changes made to repositories in the active feature
to their origin branch state, run:

.. code-block:: sh

    $ clue git reset

To do a hard reset, pass ``--hard/-h``. To reset from a different origin than
the default ``origin``, pass ``--origin=MY_REMOTE``.

``clue git squash``
^^^^^^^^^^^^^^^^^^^
If you wish to squash all commits for each branch in the active feature, run:

.. code-block:: sh

    $ clue git squash

For each repository, ``clue`` will squash all commits that come after the feature
``base`` (``master`` by default, see :ref:`base_branch`), to a single commit. (If there is only one
commit already, no action will take place for that repository).

.. warning::
    For any branch whose state before the squash was already pushed to origin,
    a subsequent ``git push -f`` will be required. Use with care, and certainly
    never use this on branches for which you are not the only active developer.

``clue git rebase``
^^^^^^^^^^^^^^^^^^^
A complementary command to the previous ``clue git squash`` is the ``rebase``
command, which will, as its name implies, rebase each branch in the active feature,
on top of the feature ``base``.

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

