Clue - Cloudify Ultimate (Development) Environment
==================================================

* ``clue`` manages your development environment.
* ``clue`` is particularly useful in managing Cloudify's development environment,
  but it is general enough to be used in other contexts.
* Your development environment is composed of:

  * The GitHub repositories in use.
  * Python packages that may reside in any repository.
* ``clue`` is implemented using ``clash``. ``clash`` is a general framework
  that turns blueprints and their workflows into CLIs.
  That means ``clue`` is mostly implemented as a blueprint but leverages some
  additional features provided by ``clash``. That is not really important but
  I think it's cool, so I'm mentioning it.

To get started, follow the :doc:`installation` and the :doc:`getting_started`
pages.

The code lives `here <https://github.com/dankilman/clue>`_.

The code for ``clash`` lives `here <https://github.com/dankilman/clash>`_.

.. toctree::
    :maxdepth: 3

    installation
    getting_started
    inputs_yaml
    branch_sets
    additional_commands
    advanced
