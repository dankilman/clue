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

import sys
import os

import sh
from path import path

from clue import tests


class TestPip(tests.BaseTest):

    def test_install(self):
        repo = 'cloudify-rest-client'
        new_version = '11111.0.1'
        repos = {'core': {repo: {}}}
        self.clue_install(repos=repos)
        pip = sh.Command(self.virtualenvs / 'cloudify' / 'bin' / 'pip')

        def extract_version():
            list_output = pip.list().stdout.strip()
            for line in list_output.split('\n'):
                if repo in line:
                    start = len('{} ('.format(repo))
                    end = line.index(',')
                    return line[start:end]
            self.fail('failed extracting version')

        setup_py = self.repos_dir / repo / 'setup.py'
        setup_py.write_text(setup_py.text().replace(extract_version(),
                                                    new_version))
        self.clue.pip.install()
        self.assertEqual(new_version, extract_version())

    def test_configure_virtualenv(self):
        repos = {'core': {'cloudify-rest-client': {}}}
        constraints = ['requests==2.5.3']
        requirements = ['xmldict==0.4.1']
        register_python_argcomplete = ['crazy-crazy']

        self.clue_install(
            repos=repos,
            constraints=constraints,
            requirements=requirements,
            register_python_argcomplete=register_python_argcomplete)

        bin_dir = self.virtualenvs / 'cloudify' / 'bin'

        pip = sh.Command(bin_dir / 'pip')
        freeze_output = pip.freeze()
        self.assertIn('cloudify-rest-client', freeze_output)
        self.assertIn('requests==2.5.3', freeze_output)
        self.assertIn('xmldict==0.4.1', freeze_output)

        clue_source_path = path(sys.executable).dirname() / 'clue'
        clue_symlink_path = bin_dir / 'clue'
        self.assertEqual(os.readlink(clue_symlink_path), clue_source_path)

        postactivate_path = bin_dir / 'postactivate'
        self.assertIn('crazy-crazy', postactivate_path.text())

        retag_cloudify_path = bin_dir / 'git-retag-cloudify'
        self.assertTrue(retag_cloudify_path.isfile())
