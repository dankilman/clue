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

import sh

from clue import tests


class TestNose(tests.BaseTest):

    def test_basic(self):
        self._test()

    def test_explicit_test_dir(self):
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._test(test_dir='i_do_not_exist')
        self.assertIn('No such file', c.exception.stdout)
        self.assertIn('i_do_not_exist', c.exception.stdout)

    def _test(self, test_dir=None):
        requirements = ['nose']
        repo = 'cloudify-rest-client'
        branch = '3.3'
        repos = {repo: {'properties': {'branch': branch}}}
        if test_dir:
            repos[repo]['python'] = {
                'test': test_dir
            }
        self.clue_install(repos=repos, requirements=requirements)
        output = self.clue.nose(repo).stdout.strip()
        self.assertTrue(output.endswith('OK'))
