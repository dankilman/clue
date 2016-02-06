Getting Started
===============

The following section describes some of the more common commands that you will
be using in your day to day interactions with ``clue``. Before you continue
with this section, make sure you quickly go over the :doc:`inputs_yaml`
section. You don't have to read all of it now. The important inputs you should
look at right now are :ref:`clone_method` and :ref:`virtualenv_name`.

``clue apply``
--------------
The first command you should run after you're done editing the ``inputs.yaml``
file is:

.. code-block:: sh

    $ clue apply

The output should look something along the lines of:

.. code-block:: sh

    ...
    [virtualenv.create] INFO: Executing: /tmp/tmpY0A_Pv-virtualenv.sh
    [cloudify-plugin-template-repo.create] WARNING: Cloning into '/home/dan/work/tmpclue/repos/cloudify-plugin-template'...
    [claw-repo.create] WARNING: Cloning into '/home/dan/work/tmpclue/repos/claw'...
    [cloudify-docker-plugin-repo.create] WARNING: Cloning into '/home/dan/work/tmpclue/repos/cloudify-docker-plugin'...
    [flask-securest-repo.create] WARNING: Cloning into '/home/dan/work/tmpclue/repos/flask-securest'...
    ...

This command does everything needed to get your environment into its desired
state (as specified by the ``inputs.yaml`` file). The first time you run it
may take a while, but this will only happen the first time.
Any time you make modifications to your ``inputs.yaml``, you should run ``clue apply``
for these changes to take place.

In addition, this command also creates a symlink to ``clue`` in the managed
virtualenv, so you would usually ``workon {{virtualenv_name}}`` when running
``clue`` commands (i.e. there is no need to ``workon {{clue_env}}`` every time
you wish to run some ``clue`` command).

It's worth mentioning that some of the configurable aspects in your managed
environment are additive. i.e. if you remove a repository, it will not be removed
from the file system, it will simply no longer be managed by ``clue``.
These inputs are: ``repos``, ``git_config``, and ``requirements``.
Also note, that removing python package definitions will not uninstall a
previously installed package.


``clue git status``
-------------------
``clue``'s main strength is in providing an easy way to manage multiple
repositories together. The first thing you need when managing multiple repositories
is to know what is their status. This is where ``clue git status`` comes into play.

Its output will look a bit like this:

.. code-block:: sh

    $ clue git status
     cloudify-dsl-parser          | master=
     docs.getcloudify.org-site    | master=
     cloudify-plugins-common      | master=
     claw-scripts                 | master=
     cloudify-agent               | master=
     cloudify-agent-packager      | master=
     cloudify-manager             | master=
     cloudify-manager-blueprints  | master=
     flask-securest               | master=
     docs.getcloudify.org         | master=
     cloudify-rest-client         | master=
     claw                         | master=
     cloudify-fabric-plugin       | master=
     cloudify-diamond-plugin      | master=
     cloudify-nodecellar-example  | master=
     cloudify-chef-plugin         | master=
     cloudify-packager            | master=
     cloudify-hello-world-example | master=
     cloudify-puppet-plugin       | master=
     cloudify-script-plugin       | master=
     cloudify-aws-plugin          | master=
     cloudify-system-tests        | master=
     cloudify-amqp-influxdb       | master=
     cloudify-plugin-template     | master=
     cloudify-docker-plugin       | master=
     cloudify-openstack-plugin    | master=
     cloudify-cli                 | master=

For each repository, its current branch name is displayed and the repo status.

Let's make this more interesting by making some changes to our repos.

.. code-block:: sh

    $ clue git status
     cloudify-dsl-parser          | 3.4m1-build=
     cloudify-cli                 | master *=
     cloudify-cli                 | M tox.ini
     cloudify-rest-client         | master %=
     cloudify-rest-client         | ?? some_new_file
     cloudify-agent               | master<
     cloudify-plugins-common      | master *+=
     cloudify-plugins-common      | D .travis.yml
     cloudify-plugins-common      | M  circle.yml

I've removed repositories that are on master and have no interesting state from
this output. Let's go over the different parts:

* The ``cloudify-dsl-parser`` repo is currently on the ``3.4m1-build`` branch.
* The ``cloudify-cli`` repo, has changes that were not staged
  for the next commit. We know this first due to the ``*`` next to the
  branch name, and also due to ``M tox.ini`` which tells us that we have a
  modification in the ``tox.ini`` file. (the real output also marks the M with
  red so that we can differentiate between staged and unstaged changes).
* The ``cloudify-rest-client`` has untracked changes. We learn this from the
  ``%`` sign, and from the ``?? some_new_file`` that tells us this file is
  untracked by git.
* The ``cloudify-agent`` repo's local master branch is behind the origin/master
  branch. (``<``)
* The ``cloudify-plugins-common`` repo has both staged (``+``) and unstaged (``*``)
  Specifically, ``.travis.yaml`` was deleted (appears in red in the actual output
  meaning this change is unstaged) and ``.circle.yaml`` was modified (appears in
  green in the actual output meaning this change is staged)

``clue git pull``
-----------------
The ``clue git pull`` command is pretty straightforward, it simply runs
``git pull`` for each managed repository. (The actual command is actually
``git pull --prune`` if git's version is smaller than ``2.0.0`` and
``git pull --prune --tags`` otherwise).

.. warning::
    For the same reason you would usually only run ``git pull`` in a clean
    git working directory, it is strongly advised to run ``clue git status``
    before running ``clue git pull`` and verify that all repositories are in
    a clean state.

``clue git checkout``
---------------------
The ``clue git checkout`` command if also pretty straightforward on the surface.
Running

.. code-block:: sh

    $ clue git checkout my_branch

will run ``git checkout my_branch`` in each managed repository. Repositories
that have this branch will switch to it and repositories that don't, well, won't.
You may see ``ERROR`` logging for checkouts that fail. This usually means that
the specified branch does not exist for that repository and can be safely ignored.
Note that it will only try switching for repositories of type ``core`` or ``plugin``.

``clue git checkout`` does, however, have a few more tricks up its sleeves.

Running ``clue git checkout default`` will checkout the default branch for each
managed repository (by default, this value is ``master``, see the :ref:`repos`
input section for more details)

Running ``clue git checkout .3.1-build`` will checkout ``3.3.1-build`` branches
for ``core`` repos and ``1.3.1-build`` branches for ``plugin`` repos. ``clue``
sees the ``.`` prefix and prepends the major number according to the repo type.
Because Cloudify no longer advances plugin versions alongside the core version,
this feature should be considered deprecated, but it is still useful when you
need to checkout a previously released Cloudify version.

The last thing ``clue git checkout`` knows how to do is checkout a branch set.
Branch sets are sets of repositories and their matching branches. They are covered
thoroughly in :doc:`branch_sets`

``clue pip install``
--------------------
The ``clue pip install`` command will run ``pip install -e .`` for each managed
python package, in the managed virtualenv. It will do so in the correct order
(based on the dependencies in the ``repos`` inputs) so that if a package depends
on another package, the latter will be installed first.

Running this command is useful in two main scenarios:

1. The last ``clue git pull`` command was executed while all core managed
repositories were on ``master`` branch, and the current milestone version was
recently bumped. Running ``clue pip install`` will bring all managed packages
to the latest version in the managed virtualenv.

2. ``clue git checkout .3.1-build`` was executed to checkout code of the ``3.3.1``
Cloudify release. In this case, a single ``clue pip install`` will install all
python packages in the current release version.

Additional Commands
-------------------
Additional commands are described in other sections because they are either
infrequently used or are considered advanced.
