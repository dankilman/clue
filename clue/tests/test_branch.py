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
import yaml

from clue import tests


git = sh.git


class TestBranch(tests.BaseTest):

    def test(self):
        branch_set1 = {
            'branch': '3.3.1-build',
            'base': '3.3.1-build',
            'repos': [
                'cloudify-dsl-parser',
                'cloudify-rest-client'
            ]
        }
        branch_set2 = {
            'repos': {
                'cloudify-dsl-parser': '3.3.1-build',
                'cloudify-rest-client': '3.3.1-build'
            }
        }
        branches_yaml = self.workdir / 'branches.yaml'
        branches_yaml.write_text(yaml.safe_dump({
            'test1': branch_set1,
            'test2': branch_set2,
        }))
        self.clue_install()
        # No real assertions for now
        self.clue.branch()
