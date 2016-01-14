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

import tempfile
import unittest
import shutil
import os
import sys

import sh
import yaml
from path import path

CLUE_CONFIG_PATH = 'CLUE_CONFIG_PATH'
WORKON_HOME = 'WORKON_HOME'
VIRTUALENVWRAPPER_PYTHON = 'VIRTUALENVWRAPPER_PYTHON'
VIRTUALENVWRAPPER_VIRTUALENV = 'VIRTUALENVWRAPPER_VIRTUALENV'


class BaseTest(unittest.TestCase):

    verbose = True
    default_clone_method = None

    def setUp(self):
        self.workdir = path(tempfile.mkdtemp(prefix='clue-tests-'))
        self.clue_conf_path = self.workdir / 'clue_conf'
        self.virtualenvs = self.workdir / 'virtualenvs'
        self.repos_dir = self.workdir / 'repos'
        os.environ[CLUE_CONFIG_PATH] = self.clue_conf_path
        os.environ[WORKON_HOME] = self.virtualenvs
        os.environ[VIRTUALENVWRAPPER_PYTHON] = sys.executable
        os.environ[VIRTUALENVWRAPPER_VIRTUALENV] = path(
            sys.executable).dirname() / 'virtualenv'
        self.previous_dir = os.getcwd()
        os.chdir(self.workdir)
        self.addCleanup(self.cleanup)
        self.clue = sh.clue.bake(_err_to_out=True)
        if self.verbose:
            self.clue = self.clue.bake(_out=lambda l: sys.stdout.write(l),
                                       _tee=True)

    def cleanup(self):
        os.chdir(self.previous_dir)
        shutil.rmtree(self.workdir, ignore_errors=True)
        for prop in [CLUE_CONFIG_PATH, WORKON_HOME, VIRTUALENVWRAPPER_PYTHON,
                     VIRTUALENVWRAPPER_VIRTUALENV]:
            os.environ.pop(prop, None)

    def _load_conf(self):
        return yaml.safe_load(self.clue_conf_path.text())

    def conf(self, name='main'):
        return self._load_conf()['configurations'][name]

    def current_env(self):
        return self._load_conf()['current']

    def storage_dir(self, name='main'):
        return path(self.conf(name)['storage_dir'])

    def editable(self, name='main'):
        return self.conf(name)['editable']

    def inputs(self, name='main'):
        return yaml.safe_load((self.storage_dir(name) / 'inputs.yaml').text())

    def set_inputs(self, inputs, name='main'):
        (self.storage_dir(name) / 'inputs.yaml').write_text(
            yaml.safe_dump(inputs))

    def blueprint(self, name='main'):
        return yaml.safe_load((self.storage_dir(name) / '.local' /
                               'resources' / 'blueprint.yaml').text())

    def clue_install(self,
                     requirements=None,
                     constraints=None,
                     repos=None,
                     clone_method=None,
                     git_config=None,
                     register_python_argcomplete=None,
                     virtualenv_name=None):
        try:
            self.clue.env.create(repos_dir=self.repos_dir)
            inputs = self.inputs()
            requirements = requirements or []
            constraints = constraints or []
            register_python_argcomplete = register_python_argcomplete or []
            repos = repos or {}
            inputs.update({
                'requirements': requirements,
                'constraints': constraints,
                'register_python_argcomplete': register_python_argcomplete,
                'repos': repos
            })
            if virtualenv_name:
                inputs['virtualenv_name'] = virtualenv_name
            if clone_method:
                inputs['clone_method'] = clone_method
            elif self.default_clone_method:
                inputs['clone_method'] = self.default_clone_method
            if git_config:
                inputs['git_config'] = git_config
            self.set_inputs(inputs)
            self.clue.init()
            return self.clue.install()
        except sh.ErrorReturnCode as e:
            self.fail(e.stdout)
