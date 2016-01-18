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

import os
import sys
import functools

import sh
import yaml
from path import path

from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation

from common import bake


def repo_operation(fn):
    @operation
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        repo = GitRepo()
        return fn(repo, *args, **kwargs)
    return wrapper


@repo_operation
def clone(repo, **_):
    repo.clone()


@repo_operation
def configure(repo, **_):
    repo.configure()


@repo_operation
def pull(repo, **_):
    repo.pull()


@repo_operation
def status(repo, **_):
    repo.status()


@repo_operation
def checkout(repo, branch, **_):
    repo.checkout(branch)


@repo_operation
def squash(repo, base, **_):
    repo.squash(base)


@repo_operation
def reset(repo, hard, origin, **_):
    repo.reset(hard, origin)


@repo_operation
def rebase(repo, base, **_):
    repo.rebase(base)


@repo_operation
def diff(repo, revision_range, **_):
    repo.diff(revision_range)


class GitRepo(object):

    def clone(self):
        git = bake(sh.git)
        ctx.instance.runtime_properties['repo_location'] = self.repo_location
        self.git_version = sh.git(version=True).stdout.strip()
        if os.path.isdir(self.repo_location):
            return
        if self.clone_method == 'https':
            clone_url = 'https://github.com/{}/{}.git'.format(
                self.organization, self.name)
        elif self.clone_method == 'ssh':
            clone_url = 'git@github.com:{}/{}.git'.format(
                self.organization, self.name)
        else:
            raise exceptions.NonRecoverableError(
                'Illegal clone method: {0}'.format(self.clone_method))
        git.clone(clone_url, self.repo_location, '-b', self.branch).wait()

    def configure(self):
        # configure commit-msg hook
        hook_path = path(self.repo_location) / '.git' / 'hooks' / 'commit-msg'
        ctx.download_resource_and_render(
                'resources/commit-msg',
                template_variables={'sys_executable': sys.executable},
                target_path=hook_path)
        os.chmod(hook_path, 0755)
        # git config
        for key, value in self.git_config.items():
            self.git.config(key, value).wait()

    def pull(self):
        kwargs = {
            'prune': True
        }
        if self.git_version >= 'git version 2.0.0':
            kwargs['tags'] = True
        self.git.pull(**kwargs).wait()

    def status(self):
        for git_prompt_path in self.git_prompt_paths:
            if os.path.exists(os.path.expanduser(git_prompt_path)):
                break
        else:
            git_prompt_path = None
        if git_prompt_path:
            script_path = ctx.download_resource_and_render(
                    'resources/git-branch-state.sh', template_variables={
                        'git_prompt_path': git_prompt_path,
                        'repo_location': self.repo_location})
            try:
                os.chmod(script_path, 0o0755)
                script = sh.Command(script_path)
                branch_state = script().stdout.strip()
            finally:
                os.remove(script_path)
        else:
            branch_state = self.current_branch
        ctx.logger.info(branch_state)
        self.git.status(s=True).wait()

    def checkout(self, branch):
        default_branch = self.branch
        active_branch_set = None
        branches = {}
        if self.branches_file.exists():
            branches = yaml.safe_load(self.branches_file.text()) or {}
        if branch in branches:
            branches_set = branches[branch]
            if all(k in branches_set for k in ['branch', 'repos']):
                if self.name in branches_set['repos']:
                    active_branch_set = branch
                    branch = branches_set['branch']
                else:
                    branch = default_branch
            else:
                if self.name in branches_set:
                    active_branch_set = branch
                    branch = branches_set[self.name]
                else:
                    branch = default_branch
        elif branch == 'default':
            branch = default_branch
        elif self.type == 'misc':
            return
        elif self.type not in ['core', 'plugin']:
            raise exceptions.NonRecoverableError('Unhandled repo type: {}'
                                                 .format(self.type))
        elif not branch:
            raise exceptions.NonRecoverableError('Branch is not defined')
        elif branch.startswith('.'):
            branch = self._fix_branch_name(branch)
        try:
            self.git.checkout(branch).wait()
            if active_branch_set:
                self.active_branch_set = active_branch_set
                self.active_branch_set_branch = branch
            else:
                del self.active_branch_set
                del self.active_branch_set_branch
        except sh.ErrorReturnCode:
            ctx.logger.error('Could not checkout branch {0}'.format(branch))

    def reset(self, hard, origin):
        if not self._validate_branch_set():
            return
        self.git.reset.bake(hard=hard)(
            '{0}/{1}'.format(origin, self.current_branch)).wait()

    def rebase(self, base):
        if not self._validate_branch_set():
            return
        try:
            base = self._fix_branch_name(base)
            self.git.rebase(base).wait()
        except Exception as e:
            ctx.logger.error('Failed rebase, aborting: {0}'.format(e))
            try:
                self.git.rebase(abort=True).wait()
            except:
                pass

    def squash(self, base):
        if not self._validate_branch_set():
            return
        if self.git_version < 'git version 1.9':
            ctx.logger.warn('git version >= 1.9 is required for squash.')
            return
        git = self.git_output
        base = self._fix_branch_name(base)
        merge_base = git.bake('merge-base', fork_point=True)(
                base).stdout.strip()
        commits = git.bake(
                'rev-list',
                ancestry_path=True,
        )('{0}..HEAD'.format(merge_base)).stdout.strip().split('\n')
        commits = [c.strip() for c in commits]
        if len(commits) == 1:
            ctx.logger.info('Single commit found. Skipping squash.')
            return
        commit_message_sha = commits[-1]
        commit_message = git.log(commit_message_sha,
                                 format='%B', n=1).stdout.strip()
        git = self.git
        ctx.logger.info(
            'Squashing with merge_base: {0} and commit message: {1}'
            .format(merge_base, commit_message))
        git.reset(merge_base, soft=True).wait()
        git.commit(message=commit_message).wait()

    def diff(self, revision_range):
        if self.type not in ['core', 'plugin']:
            return
        split_range = revision_range.split('..')
        if len(split_range) != 2:
            ctx.logger.error(
                'Invalid range supplied: {0}'.format(revision_range))
            return
        left = self._fix_branch_name(split_range[0])
        right = self._fix_branch_name(split_range[1])
        diff_range = '{0}..{1}'.format(left, right)
        try:
            self.git.diff(diff_range).wait()
        except sh.ErrorReturnCode:
            ctx.logger.error('{0} diff failed'.format(diff_range))

    @property
    def location(self):
        return os.path.expanduser(ctx.node.properties['location'])

    @property
    def name(self):
        return ctx.node.properties['name']

    @property
    def repo_location(self):
        return os.path.join(self.location, self.name)

    @property
    def organization(self):
        return ctx.node.properties['organization']

    @property
    def branch(self):
        return ctx.node.properties['branch']

    @property
    def clone_method(self):
        return ctx.node.properties['clone_method']

    @property
    def type(self):
        return ctx.node.properties['repo_type']

    @property
    def git_config(self):
        return ctx.node.properties['git_config']

    @property
    def git_prompt_paths(self):
        return ctx.node.properties['git_prompt_paths']

    @property
    def branches_file(self):
        return path(ctx.node.properties['branches_file'])

    @property
    def active_branch_set(self):
        return ctx.instance.runtime_properties.get('current_branch_set')

    @active_branch_set.setter
    def active_branch_set(self, value):
        ctx.instance.runtime_properties['current_branch_set'] = value

    @active_branch_set.deleter
    def active_branch_set(self):
        ctx.instance.runtime_properties.pop('current_branch_set', None)

    @property
    def active_branch_set_branch(self):
        return ctx.instance.runtime_properties.get('current_branch_set_branch')

    @active_branch_set_branch.setter
    def active_branch_set_branch(self, value):
        ctx.instance.runtime_properties['current_branch_set_branch'] = value

    @active_branch_set_branch.deleter
    def active_branch_set_branch(self):
        ctx.instance.runtime_properties.pop('current_branch_set_branch', None)

    @property
    def git_version(self):
        return ctx.instance.runtime_properties['git_version']

    @git_version.setter
    def git_version(self, value):
        ctx.instance.runtime_properties['git_version'] = value

    @property
    def current_branch(self):
        return self.git_output('rev-parse', '--abbrev-ref',
                               'HEAD').stdout.strip()

    @property
    def git(self):
        return self._git(log_out=True)

    @property
    def git_output(self):
        return self._git(log_out=False)

    def _git(self, log_out):
        git = sh.git
        if log_out:
            git = bake(git)
        return git.bake(
                '--no-pager',
                '--git-dir', path(self.repo_location) / '.git',
                '--work-tree', self.repo_location)

    def _validate_branch_set(self):
        if not (self.active_branch_set and self.active_branch_set_branch):
            return False
        current_branch = self.current_branch
        if self.active_branch_set_branch != current_branch:
            ctx.logger.warn(
                    'Current branch: "{0}" does not match current branch set: '
                    '"{1}" branch "{2}"'.format(current_branch,
                                                self.active_branch_set,
                                                self.active_branch_set_branch))
            return False
        return True

    def _fix_branch_name(self, branch):
        if not branch.startswith('.'):
            return branch
        if self.type not in ['core', 'plugin']:
            return branch
        template = '3{}' if self.type == 'core' else '1{}'
        return template.format(branch)
