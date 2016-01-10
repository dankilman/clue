########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

import os

import sh
from path import path

from clue import tests


class TestSetup(tests.BaseTest):

    def test_implicit_storage_dir(self):
        self._test()

    def test_explicit_storage_dir(self):
        storage_dir = self.workdir / 'storage'
        self._test(storage_dir=storage_dir)

    def test_editable_false(self):
        self._test(editable=False)

    def test_editable_true(self):
        self._test(editable=True)

    def test_existing_no_reset(self):
        self._test()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._test()
        self.assertIn('--reset to override', c.exception.stderr)

    def test_existing_reset(self):
        self._test()
        self._test(reset=True)

    def _test(self,
              storage_dir=None,
              repos_dir=None,
              editable=False,
              reset=False):
        repos_dir = repos_dir or self.workdir
        kwargs = {
            'editable': editable,
            'repos_dir': repos_dir,
            'reset': reset
        }
        if storage_dir:
            kwargs['storage_dir'] = storage_dir
        else:
            storage_dir = path(os.getcwd())
        self.clue.setup(**kwargs)
        self.assertEqual(self.storage_dir(), storage_dir)
        assertion = self.assertTrue if editable else self.assertFalse
        assertion(self.editable(), editable)
        inputs = self.inputs()
        self.assertEqual(inputs['repos_dir'], repos_dir)
        branches_dir = storage_dir / 'branches'
        self.assertEqual(inputs['branches_dir'], branches_dir)
        self.assertTrue(branches_dir.isdir())
        for key in ['repos', 'virtualenv_name', 'clone_method',
                    'virtualenvwrapper_path', 'register_python_argcomplete',
                    'requirements', 'constraints', 'git_config']:
            self.assertIn(key, inputs)
