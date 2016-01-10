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


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.workdir = path(tempfile.mkdtemp(prefix='clue-tests-'))
        self.clue_conf_path = self.workdir / 'clue_conf'
        os.environ[CLUE_CONFIG_PATH] = self.clue_conf_path
        self.previous_dir = os.getcwd()
        os.chdir(self.workdir)
        self.addCleanup(self.cleanup)
        self.clue = sh.clue
        self.clue_out = self.clue.bake(_out=lambda l: sys.stdout.write(l),
                                       _err=lambda l: sys.stderr.write(l))

    def cleanup(self):
        os.chdir(self.previous_dir)
        shutil.rmtree(self.workdir, ignore_errors=True)
        os.environ.pop(CLUE_CONFIG_PATH, None)

    def conf(self):
        return yaml.safe_load(self.clue_conf_path.text())

    def storage_dir(self):
        return path(self.conf()['storage_dir'])

    def editable(self):
        return self.conf()['editable']

    def inputs(self):
        return yaml.safe_load((self.storage_dir() / 'inputs.yaml').text())
