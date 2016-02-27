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


class TestEnvCreate(tests.BaseTest):

    def test_implicit_storage_dir(self):
        self._test()

    def test_explicit_storage_dir(self):
        storage_dir = self.workdir / 'storage'
        self._test(storage_dir=storage_dir)

    def test_explicit_env_name(self):
        self._test(name='second')

    def test_editable_false(self):
        self._test(editable=False)

    def test_editable_true(self):
        self._test(editable=True)

    def test_existing_no_reset(self):
        self._test()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._test()
        self.assertIn('--reset to override', c.exception.stdout)

    def test_existing_reset(self):
        self._test()
        self._test(reset=True)

    def test_args(self):
        custom_kwargs = {
            'clone_method': 'ssh',
            'virtualenv_name': 'my_virtualenv',
            'organization': 'my_org'
        }
        self._test(custom_kwargs=custom_kwargs)

    def _test(self,
              storage_dir=None,
              editable=False,
              reset=False,
              name=None,
              custom_kwargs=None):
        kwargs = {
            'editable': editable,
            'repos_dir': self.repos_dir,
            'reset': reset
        }
        if custom_kwargs:
            kwargs.update(custom_kwargs)
        if storage_dir:
            kwargs['storage_dir'] = storage_dir
        else:
            storage_dir = path(os.getcwd())
        if name:
            kwargs['name'] = name
        else:
            name = 'main'
        self.clue.env.create(**kwargs)
        self.assertEqual(self.current_env(), name)
        self.assertEqual(self.storage_dir(name), storage_dir)
        assertion = self.assertTrue if editable else self.assertFalse
        assertion(self.editable(name), editable)
        inputs = self.inputs(name)
        self.assertEqual(inputs['repos_dir'], self.repos_dir)
        features_yaml = storage_dir / 'features.yaml'
        self.assertEqual(inputs['features_file'], features_yaml)
        self.assertTrue(features_yaml.isfile())
        for key in ['repos', 'virtualenv_name', 'clone_method',
                    'organization', 'virtualenvwrapper_path',
                    'register_python_argcomplete', 'requirements',
                    'constraints', 'git_config']:
            self.assertIn(key, inputs)
        if custom_kwargs:
            for key, value in custom_kwargs.items():
                self.assertEqual(value, inputs[key])
