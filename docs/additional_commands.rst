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
