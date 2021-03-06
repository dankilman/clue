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


class TestCompletion(tests.BaseTest):

    def setUp(self):
        super(TestCompletion, self).setUp()
        self.clue.env.create(repos_dir=self.repos_dir)
        inputs = self.inputs()
        inputs['repos'] = {'cloudify-dsl-parser': {},
                           'cloudify-versions': {'type': 'versions'}}
        self.set_inputs(inputs)
        self.clue.init()
        self.help_args = ['-h', '--help']
        self.verbose_args = ['-v', '--verbose']

    def test_clue(self):
        builtin = ['init', 'status', 'env', 'apply'] + self.help_args
        user = ['git', 'nose', 'pip', 'install', 'feature']
        expected = builtin + user
        self.assert_completion(expected=expected)

    def test_env_create(self):
        builtin = ['--storage-dir', '-s', '--editable', '-e', '--reset', '-r',
                   '-n', '--name']
        builtin += self.help_args
        user = ['-d', '--repos-dir', '--virtualenv-name', '--clone-method',
                '--organization']
        expected = builtin + user
        self.assert_completion(expected=expected, args=['env', 'create'])

    def test_git(self):
        builtin = self.help_args
        user = ['checkout', 'diff', 'pull', 'status', 'rebase', 'squash',
                'reset']
        expected = builtin + user
        self.assert_completion(expected=expected,
                               args=['git'])

        builtin = self.verbose_args + self.help_args
        user = ['default']
        expected = builtin + user
        self.assert_completion(expected=expected, args=['git', 'checkout'])

        # TODO: add test for :: completion

    def test_feature(self):
        builtin = self.help_args

        # feature
        user = ['checkout', 'create', 'finish', 'deactivate', 'sync-repos',
                'add-repo', 'remove-repo', 'list', 'ci-status', 'compare',
                'pull-request']
        expected = builtin + user
        self.assert_completion(expected, args=['feature'])

        # prep
        features_yaml = self.workdir / 'features.yaml'
        features_yaml.write_text(yaml.safe_dump({
            'test1': {
                'repos': ['cloudify-dsl-parser', 'cloudify-versions']
            },
            'test2': {}
        }))

        # feature checkout
        user = ['test1', 'test2']
        expected = builtin + user
        self.assert_completion(expected=expected, args=['feature', 'checkout'])

        # feature create
        user = ['test1', 'test2', '-b', '--base', '--branch']
        expected = builtin + user
        self.assert_completion(expected=expected, args=['feature', 'create'])

        # feature finish --feature-name
        user = ['test1', 'test2']
        self.assert_completion(expected=user, args=['feature', 'finish',
                                                    '--feature-name'])

        # feature sync-repos --feature-name
        user = ['test1', 'test2']
        self.assert_completion(expected=user, args=['feature', 'sync-repos',
                                                    '--feature-name'])

        # feature add-repo --feature-name
        user = ['test1', 'test2']
        self.assert_completion(expected=user, args=['feature', 'add-repo',
                                                    '--feature-name'])

        # feature remove-repo --feature-name
        user = ['test1', 'test2']
        self.assert_completion(expected=user, args=['feature', 'remove-repo',
                                                    '--feature-name'])

        # feature remove-repo (before add-repo)
        # TODO: add feature remove-repo (after adding a repo)
        user = ['--feature-name', '--force', '-n', '-f']
        expected = user + builtin
        self.assert_completion(expected=expected, args=['feature',
                                                        'remove-repo'])

        # feature add-repo
        user = ['--feature-name', '-n', 'cloudify-dsl-parser',
                'cloudify-versions']
        expected = user + builtin
        self.assert_completion(expected=expected, args=['feature', 'add-repo'])

    def test_pip(self):
        builtin = self.help_args
        user = ['install']
        expected = builtin + user
        self.assert_completion(expected=expected, args=['pip'])

    def test_nose(self):
        builtin = self.help_args + self.verbose_args
        user = ['cloudify-dsl-parser']
        expected = builtin + user
        self.assert_completion(expected=expected, args=['nose'])

    def assert_completion(self, expected, args=None,
                          filter_non_options=False):
        args = args or []
        args += ["''"]
        cmd = ['clue'] + list(args)
        partial_word = cmd[-1]
        cmdline = ' '.join(cmd)
        lines = [
            'set -e',
            'eval "$(register-python-argcomplete clue)"',
            'export COMP_LINE="{}"'.format(cmdline),
            'export COMP_WORDS=({})'.format(cmdline),
            'export COMP_CWORD={}'.format(cmd.index(partial_word)),
            'export COMP_POINT={}'.format(len(cmdline)),
            '_python_argcomplete {}'.format(cmd[0]),
            'echo ${COMPREPLY[*]}'
        ]
        script_path = self.workdir / 'completions.sh'
        script_path.write_text('\n'.join(lines))
        p = sh.bash(script_path)
        completions = p.stdout.strip().split(' ')
        if filter_non_options:
            completions = [c for c in completions if c.startswith('-')]
        self.assertEqual(len(expected), len(completions),
                         'expected: {}, actual: {}'.format(expected,
                                                           completions))
        for expected_completion in expected:
            self.assertIn(expected_completion, completions)
