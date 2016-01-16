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
        if self.default_clone_method == 'ssh':
            prefix = 'git@github.com:'
        else:
            prefix = 'https://github.com/'
        self.assertEqual(origin, '{}dankilman/claw-scripts.git'.format(prefix))

    def test_clone_method_https(self):
        self._test_clone_method(clone_method='https')

    # sort of problematic testing ssh clone method
    # def test_clone_method_ssh(self):
    #     self._test_clone_method(clone_method='ssh')

    def _test_clone_method(self, clone_method):
        repo_dir = self._install(clone_method=clone_method)
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
                                 r'.*cloudify-rest-client.*\| .*master')
        self.clue.git.checkout('3.3.1-build')
        with repo_dir:
            git.reset('HEAD~')
        output = self.clue.git.status().stdout.strip()
        self.assertRegexpMatches(output,
                                 r'.*cloudify-rest-client.*\| .*3.3.1-build')
        self.assertRegexpMatches(output,
                                 r'.*cloudify-rest-client.*\| .*'
                                 r'M.*cloudify_rest_client/client.py')

    def test_checkout(self):
        (core_repo_dir,
         plugin_repo_dir,
         misc_repo_dir) = self._install_repo_types()
        test_branches = {
            'cloudify-rest-client': '3.3.1-build'
        }
        test_branches2 = {
            'branch': '3.3.1-build',
            'repos': ['cloudify-rest-client']
        }
        branches_file = self.workdir / 'branches.yaml'
        branches_file.write_text(yaml.safe_dump({
            'test': test_branches,
            'test2': test_branches2
        }))

        def assert_master():
            for repo in [core_repo_dir, plugin_repo_dir, misc_repo_dir]:
                with repo:
                    self.assertIn('master', git.status())

        def assert_custom():
            for repo, expected in [(core_repo_dir, '3.3.1-build'),
                                   (plugin_repo_dir, '1.3.1-build'),
                                   (misc_repo_dir, 'master')]:
                with repo:
                    self.assertIn(expected, git.status())

        def assert_branches_file():
            for repo, expected in [(core_repo_dir, '3.3.1-build'),
                                   (plugin_repo_dir, 'master'),
                                   (misc_repo_dir, 'master')]:
                with repo:
                    self.assertIn(expected, git.status())

        assert_master()
        self.clue.git.checkout('.3.1-build')
        assert_custom()
        self.clue.git.checkout('master')
        assert_master()
        self.clue.git.checkout('test')
        assert_branches_file()
        self.clue.git.checkout('.3.1-build')
        assert_custom()
        self.clue.git.checkout('master')
        assert_master()
        self.clue.git.checkout('test2')
        assert_branches_file()
        self.clue.git.checkout('master')
        assert_master()
        with misc_repo_dir:
            git.checkout('0.6')
            self.assertIn('0.6', git.status())
        self.clue.git.checkout('default')
        assert_master()

    def test_rebase(self):
        core_repo_dir, _, _ = self._install_repo_types()
        test_branches = {
            'cloudify-rest-client': '3.2.1-build'
        }
        branches_file = self.workdir / 'branches.yaml'
        branches_file.write_text(yaml.safe_dump({
            'test': test_branches,
        }))
        # rebase with no "active" branch set should not do anything
        output = self.clue.git.rebase('3.2.1-build').stdout.strip()
        self.assertEqual(len(output), 0)

        # only "active" branch set repos should be affected
        self.clue.git.checkout('test')
        output = self.clue.git.rebase('3.2.1-build').stdout.strip()
        self.assertEqual(len(output.split('\n')), 1)
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('Current branch 3.2.1-build is up to date.', output)

        # test repo type consideration (.2.1-build for core type should
        # transform to 3.2.1-build)
        output = self.clue.git.rebase('.2.1-build').stdout.strip()
        self.assertEqual(len(output.split('\n')), 1)
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('Current branch 3.2.1-build is up to date.', output)

        # being on a different branch then the one from the active state
        # should result in a warning, and no state change
        with core_repo_dir:
            git.checkout('3.3')
        output = self.clue.git.rebase('3.2.1-build').stdout.strip()
        self.assertEqual(len(output.split('\n')), 1)
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('does not match current branch set', output)

        # 'clue git checkout' of anything that is not a repo set, should
        # remove "active" branch set state
        self.clue.git.checkout('default')
        output = self.clue.git.rebase('3.2.1-build').stdout.strip()
        self.assertEqual(len(output), 0)

        # Unclean re-bases should be aborted
        self.clue.git.checkout('test')
        output = self.clue.git.rebase('master').stdout.strip()
        self.assertIn('Failed rebase, aborting', output)
        self.assertFalse((core_repo_dir / '.git' / 'rebase-apply').isdir())

    def test_diff(self):
        self._install_repo_types()
        self.clue.git.checkout('.3.1-build')
        self.clue.git.checkout('.3-build')
        output = self.clue.git.diff('.3-build...3.1-build').stdout.strip()
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('cloudify-script-plugin', output)
        self.assertNotIn('flask-securest', output)

    def _install(self, repo=None, repo_base=None, properties=None,
                 git_config=None, clone_method=None):
        properties = properties or {}
        repo = repo or 'cloudify-rest-client'
        if repo_base:
            repo_dir = self.repos_dir / repo_base / repo
        else:
            repo_dir = self.repos_dir / repo
        repos = {
            repo: {'python': False, 'properties': properties, 'type': 'core'}
        }
        self.clue_install(repos=repos, git_config=git_config,
                          clone_method=clone_method)
        return repo_dir

    def _install_repo_types(self):
        core_repo = 'cloudify-rest-client'
        core_repo_dir = self.repos_dir / core_repo
        plugin_repo = 'cloudify-script-plugin'
        plugin_repo_dir = self.repos_dir / plugin_repo
        misc_repo = 'flask-securest'
        misc_repo_dir = self.repos_dir / misc_repo
        repos = {
            core_repo: {'type': 'core', 'python': False},
            plugin_repo: {'type': 'plugin', 'python': False},
            misc_repo: {'python': False}
        }
        self.clue_install(repos=repos)
        return core_repo_dir, plugin_repo_dir, misc_repo_dir
