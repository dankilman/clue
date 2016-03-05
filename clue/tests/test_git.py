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

        with repo_dir:
            # Test commit message hook
            jira = 'CFY-10000'
            branch = '{}-hello-world'.format(jira)
            commit_message = 'my commit message'
            git.checkout('-b', branch)
            (repo_dir / 'tox.ini').write_text('testing 123')
            git.commit('-am', commit_message)
            self.assertEqual(self._log_message(),
                             '{} {}'.format(jira, commit_message))

            # Test git config
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
        core_repo_dir, _, _ = self._install_repo_types_with_branches()
        output = self.clue.git.status().stdout.strip()
        self.assertRegexpMatches(output,
                                 r'.*cloudify-rest-client.*\| .*master')
        self.assertIn('cloudify-script-plugin', output)
        self.assertIn('flask-securest', output)
        self.clue.git.checkout('.3.1-build')
        with core_repo_dir:
            git.reset('HEAD~')
        output = self.clue.git.status().stdout.strip()
        self.assertRegexpMatches(output,
                                 r'.*cloudify-rest-client.*\| .*3.3.1-build')
        self.assertRegexpMatches(output,
                                 r'.*cloudify-rest-client.*\| .*'
                                 r'M.*cloudify_rest_client/client.py')
        # test active
        with core_repo_dir:
            git.reset('--hard', 'HEAD')
        self.clue.feature.checkout('test')
        output = self.clue.git.status(active=True).stdout.strip()
        self.assertIn('cloudify-rest-client', output)
        self.assertNotIn('flask-securest', output)
        self.assertNotIn('cloudify-script-plugin', output)

    def test_checkout(self):
        (core_repo_dir,
         plugin_repo_dir,
         misc_repo_dir) = self._install_repo_types()
        test_branches = {
            'repos': {
                'cloudify-rest-client': '3.3.1-build'
            }
        }
        test_branches2 = {
            'branch': '3.3.1-build',
            'repos': ['cloudify-rest-client']
        }
        features_file = self.workdir / 'features.yaml'
        features_file.write_text(yaml.safe_dump({
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

        def assert_features_file():
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
        self.clue.feature.checkout('test')
        assert_features_file()
        self.clue.git.checkout('.3.1-build')
        assert_custom()
        self.clue.git.checkout('master')
        assert_master()
        self.clue.feature.checkout('test2')
        assert_features_file()
        self.clue.git.checkout('master')
        assert_master()
        with misc_repo_dir:
            git.checkout('0.6')
            self.assertIn('0.6', git.status())
        self.clue.git.checkout('default')
        assert_master()

    def test_rebase(self):
        branch = '3.2.1-build'
        base = branch
        core_repo_dir, _, _ = self._install_repo_types_with_branches(
            branch=branch,
            base=base)

        # rebase with no "active" feature should not do anything
        output = self.clue.git.rebase().stdout.strip()
        self.assertEqual(len(output), 0)

        # only "active" feature repos should be affected
        self.clue.feature.checkout('test')
        output = self.clue.git.rebase().stdout.strip()
        self.assertEqual(len(output.split('\n')), 1)
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('Current branch 3.2.1-build is up to date.', output)

        # test repo type consideration (.2.1-build for core type should
        # transform to 3.2.1-build)
        output = self.clue.git.rebase().stdout.strip()
        self.assertEqual(len(output.split('\n')), 1)
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('Current branch 3.2.1-build is up to date.', output)

        # being on a different branch then the one from the active state
        # should result in a warning, and no state change
        with core_repo_dir:
            git.checkout('3.3')
        output = self.clue.git.rebase().stdout.strip()
        self.assertEqual(len(output.split('\n')), 1)
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('does not match the active feature branch', output)

        # Unclean re-bases should be aborted
        self._update_features_yaml(branch=branch, base='master')
        self.clue.feature.checkout('test')
        output = self.clue.git.rebase().stdout.strip()
        self.assertIn('Failed rebase, aborting', output)
        self.assertFalse((core_repo_dir / '.git' / 'rebase-apply').isdir())

        # Test default master base
        self._update_features_yaml(branch='master')
        self.clue.feature.checkout('test')
        output = self.clue.git.rebase().stdout.strip()
        self.assertEqual(len(output.split('\n')), 1)
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('Current branch master is up to date.', output)

    def test_squash(self):
        branch = 'test_branch'
        core_repo_dir, _, _ = self._install_repo_types_with_branches(
            branch=branch)

        # squash with no "active" feature should not do anything
        output = self.clue.git.squash().stdout.strip()
        self.assertEqual(len(output), 0)

        with core_repo_dir:
            git.checkout.bake(b=True)(branch)
            temp_file = core_repo_dir / 'temp'
            temp_file.write_text('temp')
            commit_message = 'real_commit'
            git.add(temp_file)
            git.commit('-m', commit_message)
            initial_sha = self._current_sha()
            self._make_modifications(core_repo_dir)
            after_commits_sha = self._current_sha()
            self.assertNotEqual(initial_sha, after_commits_sha)

        # squash command requires active feature
        self.clue.feature.checkout('test')

        # Test squash when there is more than 1 commit
        self.clue.git.squash()
        after_squash_sha = self._current_sha()
        with core_repo_dir:
            self.assertNotEqual(after_commits_sha, self._current_sha())
            current_commit_message = self._log_message(after_squash_sha)
            self.assertEqual(commit_message, current_commit_message)

        # Test squash with no expected change (previous changes were squashed
        # into 1 commit)
        self.clue.git.squash()
        self.assertEqual(after_squash_sha, self._current_sha())

        # test .3.1-build => 3.3.1-build transformation by examining
        # error message of illegal squash
        self._update_features_yaml(branch=branch, base='.3.1-build')
        self.clue.feature.checkout('test')
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self.clue.git.squash()
        self.assertIn('3.3.1-build', c.exception.stdout)

    def test_reset(self):
        core_repo_dir, _, _ = self._install_repo_types_with_branches()

        # reset with no "active" feature should not do anything
        output = self.clue.git.reset().stdout.strip()
        self.assertEqual(len(output), 0)

        # reset command requires active feature
        self.clue.feature.checkout('test')

        def test_reset(hard=False, origin=None):
            with core_repo_dir:
                initial_sha = self._current_sha()
                self._make_modifications(repo_dir=core_repo_dir,
                                         skip_last_commit=hard)
                self.assertNotEqual(initial_sha, self._current_sha())
            command = self.clue.git.reset.bake(hard=hard)
            if origin:
                command.bake(origin=origin)
            output = command().stdout.strip()
            if hard:
                self.assertNotIn('Unstaged changes', output)
            with core_repo_dir:
                self.assertEqual(initial_sha, self._current_sha())

        test_reset(hard=False)
        test_reset(hard=True)
        test_reset(origin='origin')

    def test_diff(self):
        core, _, _ = self._install_repo_types_with_branches()
        self.clue.git.checkout('.3.1-build')
        self.clue.git.checkout('.3-build')
        revision_range = '.3-build...3.1-build'
        # test revision range
        output = self.clue.git.diff(r=revision_range).stdout.strip()
        self.assertIn('cloudify-rest-client', output)
        self.assertIn('cloudify-script-plugin', output)
        self.assertNotIn('flask-securest', output)
        self.assertNotIn('ERROR', output)
        self.clue.feature.checkout('test')
        # test active
        output = self.clue.git.diff(r=revision_range, a=True).stdout.strip()
        self.assertIn('cloudify-rest-client', output)
        self.assertNotIn('cloudify-script-plugin', output)
        self.assertNotIn('flask-securest', output)
        self.assertNotIn('ERROR', output)
        with core:
            git.reset('HEAD~')
        # test plain
        output = self.clue.git.diff(a=True).stdout.strip()
        self.assertIn('cloudify-rest-client', output)
        self.assertNotIn('ERROR', output)
        output = self.clue.git.diff(a=True, c=True).stdout.strip()
        self.assertEqual(0, len(output))
        # test cached
        with core:
            git.add('.')
        output = self.clue.git.diff(a=True, c=True).stdout.strip()
        self.assertIn('cloudify-rest-client', output)
        self.assertNotIn('ERROR', output)
        output = self.clue.git.diff(a=True).stdout.strip()
        self.assertEqual(0, len(output))

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

    def _install_repo_types_with_branches(self, branch='3.2.1-build',
                                          base=None):
        git_config = {
            'user.name': 'John Doe',
            'user.email': 'john.doe@example.com'
        }
        core, plugin, misc = self._install_repo_types(git_config=git_config)
        self._update_features_yaml(branch, base)
        return core, plugin, misc

    def _update_features_yaml(self, branch, base=None):
        test_branches = {
            'repos': {
                'cloudify-rest-client': branch
            }
        }
        if base:
            test_branches['base'] = base
        features_file = self.workdir / 'features.yaml'
        features_file.write_text(yaml.safe_dump({
            'test': test_branches,
        }))

    def _install_repo_types(self, git_config=None):
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
        self.clue_install(repos=repos, git_config=git_config)
        return core_repo_dir, plugin_repo_dir, misc_repo_dir

    def _current_sha(self):
        return git('rev-parse', 'HEAD').stdout.strip()

    def _make_modifications(self, repo_dir, count=3, skip_last_commit=False):
        with repo_dir:
            tox_ini = repo_dir / 'tox.ini'
            for i in range(count):
                tox_ini_text = tox_ini.text()
                tox_ini_text = '{}\n{}'.format(tox_ini_text, i)
                tox_ini.write_text(tox_ini_text)
                if i == count - 1 and skip_last_commit:
                    continue
                git.commit('-am', str(i))

    def _log_message(self, sha=None):
        if not sha:
            sha = self._current_sha()
        return git.bake(no_pager=True).log(sha, n=1,
                                           format='%B').stdout.strip()
