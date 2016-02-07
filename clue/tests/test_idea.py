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


class TestIdea(tests.BaseTest):

    def test_no_project_dir(self):
        repo = 'cloudify-rest-client'
        repos = {repo: {}}
        repo_dir = self.repos_dir / repo
        self.clue_install(repos=repos)
        self.assertFalse((repo_dir / '{}.iml'.format(repo)).exists())

    def test_project_dir(self):
        repo1 = 'cloudify-rest-client'
        repo2 = 'cloudify-dsl-parser'
        repo3 = 'cloudify-manager-blueprints'
        repo4 = 'claw-scripts'
        repo5 = 'cloudify-plugins-common'
        repos = {
            repo1: {},
            repo2: {'properties': {'project_dir': True}},
            repo3: {'python': False},
            repo4: {'python': False,
                    'properties': {'resources': True,
                                   'organization': 'dankilman'}},
            repo5: {'python': False,
                    'properties': {'resources': ['cloudify']}}
        }
        repo1_dir = self.repos_dir / repo1
        repo2_dir = self.repos_dir / repo2
        repo3_dir = self.repos_dir / repo3
        repo4_dir = self.repos_dir / repo4
        repo5_dir = self.repos_dir / repo5
        self.clue_install(repos=repos)
        self.assertTrue((repo1_dir / '{}.iml'.format(repo1)).exists())
        self.assertTrue((repo2_dir / '{}.iml'.format(repo2)).exists())
        self.assertFalse((repo3_dir / '{}.iml'.format(repo3)).exists())
        self.assertTrue((repo4_dir / '{}.iml'.format(repo4)).exists())
        self.assertFalse((repo5_dir / '{}.iml'.format(repo5)).exists())
        self.assertTrue(
            (repo5_dir / 'cloudify/cloudify.iml'.format(repo5)).exists())
        idea_dir = repo2_dir / '.idea'
        self.assertTrue(idea_dir.exists())
        modules_xml = idea_dir / 'modules.xml'
        vcs_xml = idea_dir / 'vcs.xml'
        misc_xml = idea_dir / 'misc.xml'
        for f in [modules_xml, vcs_xml, misc_xml]:
            self.assertTrue(f.exists())
        self.assertIn('project-jdk-name="cloudify"', misc_xml.text())
        vcs = vcs_xml.text()
        self.assertIn('cloudify-rest-client', vcs)
        self.assertIn('cloudify-dsl-parser', vcs)
        self.assertIn('cloudify-plugins-common', vcs)
        self.assertIn('claw-scripts', vcs)
        self.assertIn('cloudify-manager-blueprints', vcs)
        modules = modules_xml.text()
        self.assertIn('cloudify-rest-client', modules)
        self.assertIn('cloudify-dsl-parser', modules)
        self.assertIn('cloudify-plugins-common/cloudify', modules)
        self.assertIn('claw-scripts', modules)
        self.assertNotIn('cloudify-manager-blueprints', modules)
