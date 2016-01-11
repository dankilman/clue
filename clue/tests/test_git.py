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


git = sh.git


class TestGit(tests.BaseTest):

    def test_clone_location(self):
        repo_base = 'custom'
        repo_dir = self._install(
            repo_base=repo_base,
            properties={'location': str(self.repos_dir / 'custom')})
        with repo_dir:
            self.assertIn('master', git.status())

    def test_clone_branch(self):
        repo_dir = self._install(properties={'branch': '3.3.1-build'})
        with repo_dir:
            self.assertIn('3.3.1-build', git.status())

    def test_clone_organization(self):
        repo_dir = self._install(
            repo='claw-scripts',
            properties={'organization': 'dankilman'})
        with repo_dir:
            origin = git.config('remote.origin.url').stdout.strip()
        self.assertEqual(origin,
                         'https://github.com/dankilman/claw-scripts.git')

    def test_clone_method_https(self):
        self._test_clone_method(clone_method='https')

    def test_clone_method_ssh(self):
        self._test_clone_method(clone_method='ssh')

    def _test_clone_method(self, clone_method):
        repo_dir = self._install()
        with repo_dir:
            origin = git.config('remote.origin.url').stdout.strip()
        if clone_method == 'ssh':
            prefix = 'git@github.com:'
        elif clone_method == 'https':
            prefix = 'https://github.com/'
        else:
            self.fail(clone_method)
        self.assertEqual(origin, '{}cloudify-cosmo/cloudify-rest-client.git'
                                 .format(prefix))

    def test_configure(self):
        name = 'John Doe'
        email = 'john@example.com'
        repo_dir = self._install(git_config={
            'user.name': name,
            'user.email': email
        })
        commit_msg_path = repo_dir / '.git' / 'hooks' / 'commit-msg'
        self.assertTrue(commit_msg_path.exists())
        self.assertEqual(commit_msg_path.stat().st_mode & 0755, 0755)
        with repo_dir:
            self.assertEqual(name, git.config('user.name').stdout.strip())
            self.assertEqual(email, git.config('user.email').stdout.strip())

    def test_pull(self):
        repo_dir = self._install()
        with repo_dir:
            initial_status = git.status().stdout.strip()
            git.reset('HEAD~')
            self.assertNotEqual(initial_status, git.status().stdout.strip())
            git.reset(hard=True)
        self.clue.git.pull()
        with repo_dir:
            self.assertEqual(initial_status, git.status().stdout.strip())

    def test_status(self):
        repo_dir = self._install()
        output = self.clue.git.status().stdout.strip()
        self.assertRegexpMatches(output,
                                 r'.*cloudify-rest-client.*\| master')
        self.clue.git.checkout('3.3.1-build')
        with repo_dir:
            git.reset('HEAD~')
        output = self.clue.git.status().stdout.strip()
        self.assertRegexpMatches(output,
                                 r'.*cloudify-rest-client.*\| 3.3.1-build')
        self.assertRegexpMatches(output,
                                 r'.*cloudify-rest-client.*\| '
                                 r'M cloudify_rest_client/client.py')

    def _install(self, repo=None, repo_base=None, properties=None,
                 git_config=None):
        properties = properties or {}
        repo = repo or 'cloudify-rest-client'
        if repo_base:
            repo_dir = self.repos_dir / repo_base / repo
        else:
            repo_dir = self.repos_dir / repo
        repos = {
            'core': {
                repo: {'python': False,
                       'properties': properties}
            }
        }
        self.clue_install(repos=repos, git_config=git_config)
        return repo_dir
