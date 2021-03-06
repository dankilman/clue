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

from clue import tests


class TestInputs(tests.BaseTest):

    def test_virtualenv_name(self):
        virtualenv_name = 'clue_test_virtualenv'
        self.clue_install(virtualenv_name=virtualenv_name)
        self.assertTrue((self.virtualenvs / virtualenv_name).isdir())

    def test_organization(self):
        repos = {'claw-scripts': {'python': False}}
        organization = 'dankilman'
        self.clue_install(organization=organization, repos=repos)
        self.assertTrue((self.repos_dir / 'claw-scripts').isdir())
