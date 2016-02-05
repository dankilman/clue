Getting Started
===============

Basic Usage
-----------

The following section describes some of the more common commands that you will
be using in your day to day interactions with ``clue``. Before you continue
with this section, make sure you read the ``inputs.yaml`` section below.
You don't have to read all of it now. The important inputs you should look at
right now are :ref:`clone_method` and :ref:`virtualenv_name`.


``inputs.yaml``
---------------

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
