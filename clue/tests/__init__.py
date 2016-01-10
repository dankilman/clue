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
        self.clue = sh.clue
        if self.verbose:
            self.clue = self.clue.bake(_out=lambda l: sys.stdout.write(l),
                                       _err=lambda l: sys.stderr.write(l),
                                       _tee=True)

    def cleanup(self):
        os.chdir(self.previous_dir)
        shutil.rmtree(self.workdir, ignore_errors=True)
        for prop in [CLUE_CONFIG_PATH, WORKON_HOME, VIRTUALENVWRAPPER_PYTHON,
                     VIRTUALENVWRAPPER_VIRTUALENV]:
            os.environ.pop(prop, None)

    def conf(self):
        return yaml.safe_load(self.clue_conf_path.text())

    def storage_dir(self):
        return path(self.conf()['storage_dir'])

    def editable(self):
        return self.conf()['editable']

    def inputs(self):
        return yaml.safe_load((self.storage_dir() / 'inputs.yaml').text())

    def set_inputs(self, inputs):
        (self.storage_dir() / 'inputs.yaml').write_text(yaml.safe_dump(inputs))

    def blueprint(self):
        return yaml.safe_load((self.storage_dir() / '.local' / 'resources' /
                               'blueprint.yaml').text())

    def clue_install(self, requirements=None, repos=None):
        self.clue.setup(repos_dir=self.repos_dir)
        inputs = self.inputs()
        requirements = requirements or []
        repos = repos or {}
        inputs.update({
            'requirements': requirements,
            'repos': repos
        })
        self.set_inputs(inputs)
        self.clue.init()
        return self.clue.install()
