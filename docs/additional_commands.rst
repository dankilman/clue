Additional Commands
===================

What follows are additional ``clue`` commands in no particular order.

``clue nose PACKAGE_NAME``
^^^^^^^^^^^^^^^^^^^^^^^^^^
You can run ``nosetests`` on any python package that is managed by ``clue``.
For example:

.. code-block:: sh

    $ clue nose cloudify-dsl-parser

This is (almost) equivalent to running

.. code-block:: sh

    $ cd /path/to/cloudify-dsl-parser
    $ nosetests --nocapture --nologcapture --verbose .

If you wish to use a directory relative to the basedir you can pass the ``test``
property to the ``python`` part of the a repo configuration in ``inputs.yaml``

.. code-block:: yaml

    repos:
      cloudify-dsl-parser:
        type: core
        python:
          test: dsl_parser/tests

Running

.. code-block:: sh

    $ clue nose cloudify-dsl-parser

now, is (almost) equivalent to running:

.. code-block:: sh

    $ cd /path/to/cloudify-dsl-parser
    $ nosetests --nocapture --nologcapture --verbose dsl_parser/tests

``clue git diff``
^^^^^^^^^^^^^^^^^
You can use ``clue git diff`` to perform an aggregated ``git diff`` command
on all repositories or only repositories that are part of the *active branch set*

The ``clue git diff`` command supports to variants.

1. ``git diff [--cached]`` which can be used to perform a simple ``git diff``
   command on each repository.

2. ``git diff LEFT..RIGHT`` which can be used to run a ``git diff`` comparison
   between two branches or similar.

To run the diff command only on active branch set repositories, pass the
``--active/-a`` flag.

``clue status``
^^^^^^^^^^^^^^^
The ``clue status`` commands prints out details about the current ``clue``
environment and details about the repositories dir and virtualenv root.

The output will look something like:

.. code-block:: sh

    $ clue status
    env:
      current: main
      editable: false
      storage_dir: /home/dan/work/clue
    outputs:
      repositories: /home/dan/dev/cloudify
      virtualenv: /home/dan/.virtualenvs/cloudify

The previous output is in fact valid yaml. You can pass ``--json/-j`` to get
the output in JSON format.
