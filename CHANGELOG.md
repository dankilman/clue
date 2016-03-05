# 0.34

## Breaking Changes
* `branches.yaml` is now named `features.yaml`. The easiest way to migrate the
   current configuration is to manually rename the file, and edit the `inputs.yaml`
   file so the previous `branches_file` input, is now named `features_file` and
   points to the correct file. Afterward, run `clue apply` and you should be good
   to go.
* `clue git checkout {{branch_set_name}}` is now `clue feature checkout {{feature_name}}`
  (other `clue git checkout` commands work with no changes).
* different branch names in feature definition is no longer supported. Support
  may be re-added in the future.

## What's New
* A new `feature` subcommand has been added. See [Features](http://clue.readthedocs.org/en/latest/features.html) for details.
* Default inputs now include the `je` and `cloudify-versions` repositories.
  `je` is a tool used to manage system tests in jenkins. `cloudify-versions`
  is used to support the new `clue git checkout ::` feature.
* If the `cloudify-versions` repo is configured in the `inputs.yaml` file with
  `versions` type, `clue git checkout ::{TAG/BRANCH}` will checkout all components
  configured in the `versions.yaml` file for that tag/branch, it will also checkout
  `TAG/BRANCH` for all `core` repositories. Try it out to understand what it means.
  Note that bash completion is implemented for this feature and can be activated
  after typing ``clue git checkout ::`.
