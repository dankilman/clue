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

import json

from clue import tests


class TestStatus(tests.BaseTest):

    def test(self):
        self.clue_install()
        status = self.clue.status().stdout.strip()
        json_status = json.loads(self.clue.status(json=True).stdout.strip())
        self.assertIn('current: main', status)
        self.assertIn('repositories: {}'.format(self.repos_dir), status)
        self.assertIn('virtualenv: {}'.format(self.virtualenvs / 'cloudify'),
                      status)
        self.assertEqual(json_status, {
            'env': {
                'current': 'main',
                'storage_dir': self.storage_dir(),
                'editable': self.editable()
            },
            'outputs': {
                'repositories': self.repos_dir,
                'virtualenv': self.virtualenvs / 'cloudify'
            }
        })
