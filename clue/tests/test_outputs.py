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


class TestOutputs(tests.BaseTest):

    def test(self):
        self.clue.setup(repos_dir=self.workdir / 'repos')
        inputs = self.inputs()
        inputs['repos'] = {}
        inputs['requirements'] = []
        self.set_inputs(inputs)
        self.clue.init()
        self.clue_out.install()
        outputs = self.clue.outputs().stdout.strip()
        json_outputs = json.loads(self.clue.outputs(json=True).stdout.strip())
        self.assertIn('repositories: {}'.format(self.workdir / 'repos'),
                      outputs)
        self.assertIn(
            'virtualenv: {}'.format(self.workdir / 'virtualenvs' / 'cloudify'),
            outputs)
        self.assertEqual(json_outputs, {
            'repositories': self.workdir / 'repos',
            'virtualenv': self.workdir / 'virtualenvs' / 'cloudify'
        })
