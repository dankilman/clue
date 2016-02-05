Getting Started
===============

Basic Usage
-----------

The following section describes some of the more common commands that you will
be using in your day to day interactions with ``clue``. Before you continue
with this section, make sure you read the ``inputs.yaml`` section below.
You don't have to read all of it now. The important inputs you should look at
right now are :ref:`clone_method` and :ref:`virtualenv_name`.

``clue apply``
^^^^^^^^^^^^^^
The first command you should run after your done editing the ``inputs.yaml`` file
is:

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
environment, are additive. i.e. if you remove a repository, it will not be removed
from the file system, it will simply no longer be managed by ``clue``.
These inputs are: ``repos``, ``git_config``, and ``requirements``.
Also note, that removing python package definitions will not uninstall a
previously installed package.


``clue git status``
^^^^^^^^^^^^^^^^^^^
``clue``'s main strength is in providing an easy way to manage multiple
repositories together. The first thing you need when managing multiple repositories
is to know what is their status. This is where ``clue git status`` comes into play.

It's output will look a bit like this:

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

For each repository, it's current branch name is displayed and the repo status.

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
^^^^^^^^^^^^^^^^^
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
^^^^^^^^^^^^^^^^^^^^^
TODO

``clue pip install``
^^^^^^^^^^^^^^^^^^^^
TODO

Additional Commands
^^^^^^^^^^^^^^^^^^^
Additional commands are described in other sections because they are either
infrequently used or are considered advanced.

inputs.yaml
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

.. _clone_method:

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

``repos``
^^^^^^^^^
The ``repos`` input is a dictionary that specifies all repositories that are
managed by ``clue`` and for each, the python packages it contains.
By default, each repository is assumed to also represent a python package but
this can be overridden as explain in the following section.

*   Each entry in this dictionary represents a single GitHub repository, for example:

    .. code-block:: yaml

        repos:
          cloudify-rest-client:
            type: core

    The above represents an environment that contains a single
    repository, ``cloudify-rest-client``. The organization is derived from the
    ``organization`` input. The type ``core`` should be specified for all Cloudify
    repositories who's version advances with the Cloudify version. We supplied
    no ``python`` property, so be default, ``clue`` assumed this repository represents
    a python package that is ``pip`` installable with no additional dependencies.

*   Use the ``dependencies`` property to specify additional python dependencies a
    python package has, for example:

    .. code-block:: yaml

        repos:
          cloudify-rest-client:
            type: core

          cloudify-plugins-common:
            type: core
            python:
              dependencies:
              - cloudify-rest-client

    The above builds upon the previous example and adds the ``cloudify-plugins-common``
    repository. Notice that it specifies a dependency on the ``cloudify-rest-client``
    python package.

*   To tell ``clue`` that a certain repository does not represent a python package,
    specify ``python: false``.

    .. code-block:: yaml

        repos:
          docs.getcloudify.org:
            python: false


*   ``clue`` automatically add a python dependency on ``cloudify-plugins-common``
    for repositories of type ``plugin``.

    .. code-block:: yaml

        repos:
          cloudify-openstack-plugin:
            type: plugin

*   A repository that represents a python package and is not of ``core`` or ``plugin``
    type, can be specified like this:

    .. code-block:: yaml

        repos:
          flask-securest: {}

*   You can override the default organization and parent directory for repositories
    like this:

    .. code-block:: yaml

          claw-scripts:
            properties:
              organization: dankilman
              location: /path/to/parent/repo/directory
            python: false

    The above tells ``clue`` to clone the ``claw-scripts`` repository from the ``dankilman``
    organization and to use ``/path/to/parent/repo/directory`` as its base dir.

*   There may be cases where a certain repository contains one or more python
    packages that are not directly located in its root. In such cases, you can
    specify a list of package definitions to the ``python`` property, like this:

    .. code-block:: yaml

        cloudify-manager:
          python:
          - name: cloudify-rest-service
            path: rest-service
            dependencies:
            - cloudify-dsl-parser
            - flask-securest
          - name: cloudify-workflows
            path: workflows
            dependencies:
            - cloudify-plugins-common


``repos_dir``
^^^^^^^^^^^^^
The root directory to which all managed GitHub repositories will be cloned.
The value for this inputs was supplied in the ``clue env create`` command.
This value can be changed at any time to have ``clue`` manage a different
root directory.

.. note::
    As explained in the ``repos`` input section, you can override the base dir
    for each managed repository specifically. This allows you to have certain
    repositories that will be managed by ``clue`` but will be located in base
    directories.

``requirements``
^^^^^^^^^^^^^^^^
A list of additional requirements that will be installed in the managed virtualenv.
The default value contains ``flake8``, ``tox``, ``nose`` and a few other testing
frameworks. You can update this list to your liking.

.. _virtualenv_name:

``virtualenv_name``
^^^^^^^^^^^^^^^^^^^
The name of the ``virtualenvwrapper`` virtualenv. The default value is ``cloudify``.
If this virtualenv already exists, ``clue`` will make use of it, otherwise, it will
create a new virtualenv using ``mkvirtualenv {{virtualenv_name}}``.

``virtualenvwrapper_path``
^^^^^^^^^^^^^^^^^^^^^^^^^^
If ``virtualenvwrapper`` is installed system wide, the default value
``virtualenvwrapper.sh`` can be used. Otherwise, a full path to this script
should be supplied.
