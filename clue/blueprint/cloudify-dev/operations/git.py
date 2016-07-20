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
import os
import sys

import sh
import yaml
from path import path

from cloudify import ctx
from cloudify.workflows import ctx as workflow_ctx
from cloudify import exceptions
from cloudify.decorators import operation
from cloudify.decorators import workflow

from common import bake


class GitRepo(object):

    def clone(self):
        git = bake(sh.git)
        self.runtime_properties['repo_location'] = str(self.repo_location)
        self.git_version = sh.git(version=True).stdout.strip()
        if self.repo_location.isdir():
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
        hook_path = self.repo_location / '.git' / 'hooks' / 'commit-msg'
        ctx.download_resource_and_render(
            'resources/commit-msg',
            template_variables={'sys_executable': sys.executable},
            target_path=hook_path)
        os.chmod(hook_path, 0o755)
        # git config
        for key, value in self.git_config.items():
            self.git.config(key, value).wait()
        if self.type == 'versions':
            self.versions_repo_location = self.repo_location

    def pull(self):
        try:
            self.git_output('rev-parse', '@{u}')
        except sh.ErrorReturnCode:
            ctx.logger.info('No upstream defined. Skipping pull.')
            return
        kwargs = {'prune': True}
        if self.git_version >= 'git version 2.0.0':
            kwargs['tags'] = True
        self.git.pull(**kwargs).wait()

    def status(self, active):
        if active and not self.active_feature.branch:
            return
        for git_prompt_path in self.git_prompt_paths:
            if git_prompt_path.expanduser().exists():
                break
        else:
            git_prompt_path = None
        if git_prompt_path:
            script_path = ctx.download_resource_and_render(
                'resources/git-branch-state.sh', template_variables={
                    'git_prompt_path': git_prompt_path,
                    'repo_location': self.repo_location})
            try:
                os.chmod(script_path, 0o755)
                script = sh.Command(script_path)
                branch_state = script().stdout.strip()
            finally:
                os.remove(script_path)
        else:
            branch_state = self.current_branch
        ctx.logger.info(branch_state)
        self.git.status(s=True).wait()

    def checkout(self, branch):
        versions_prefix = '::'
        default_branch = self.branch
        active_feature = self.active_feature
        if branch.startswith(versions_prefix):
            versions_branch = branch[len(versions_prefix):]
            components = self._read_versions_file(versions_branch)
            if self.name in components:
                branch = components[self.name]
            elif self.type in ['core', 'versions']:
                branch = versions_branch
            else:
                branch = default_branch
        elif active_feature.name == branch:
            branch = active_feature.branch
            base_branch = active_feature.base
            if not branch:
                if base_branch.startswith(versions_prefix):
                    versions_branch = base_branch[len(versions_prefix):]
                    components = self._read_versions_file(versions_branch)
                    if self.name in components:
                        branch = components[self.name]
                    elif self.type in ['core', 'versions']:
                        branch = versions_branch
                    else:
                        branch = default_branch
                else:
                    if self.type in ['core', 'versions']:
                        branch = base_branch
                    else:
                        branch = default_branch
        elif branch == 'default':
            branch = default_branch
        elif self.type == 'misc':
            return
        elif self.type not in ['core', 'plugin', 'versions']:
            raise exceptions.NonRecoverableError('Unhandled repo type: {}'
                                                 .format(self.type))
        elif not branch:
            raise exceptions.NonRecoverableError('Branch is not defined')
        elif branch.startswith('.'):
            branch = self._fix_branch_name(branch)
        try:
            if self.current_branch != branch:
                self.git.checkout(branch).wait()
        except sh.ErrorReturnCode:
            ctx.logger.error('Could not checkout branch {0}'.format(branch))

    def reset(self, hard, origin):
        if not self.validate_active_feature():
            return
        self.git.reset.bake(hard=hard)(
            '{0}/{1}'.format(origin, self.current_branch)).wait()

    def rebase(self):
        if not self.validate_active_feature():
            return
        base = self.active_feature.base
        try:
            base = self._fix_branch_name(base)
            self.git.rebase(base).wait()
        except Exception as e:
            ctx.logger.error('Failed rebase, aborting: {0}'.format(e))
            try:
                self.git.rebase(abort=True).wait()
            except:
                pass

    def squash(self):
        if not self.validate_active_feature():
            return
        if self.git_version < 'git version 1.9':
            ctx.logger.warn('git version >= 1.9 is required for squash.')
            return
        git = self.git_output
        base = self.active_feature.base
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

    def diff(self, revision_range, cached, active):
        if active and not self.active_feature.branch:
            return
        if self.type not in ['core', 'plugin']:
            return

        args = []
        kwargs = {
            'cached': cached
        }

        if revision_range:
            split_by = '..'
            split_range = revision_range.split(split_by)
            if len(split_range) != 2:
                ctx.logger.error(
                    'Invalid range supplied: {0}'.format(revision_range))
                return
            left = self._fix_branch_name(split_range[0])
            right = self._fix_branch_name(split_range[1])
            diff_range = '{0}{1}{2}'.format(left, split_by, right)
            args.append(diff_range)

        try:
            self.git.diff(*args, **kwargs).wait()
        except sh.ErrorReturnCode:
            ctx.logger.error('{0}, {1} diff failed'.format(args, kwargs))

    def create_branch(self, branch, base):
        if not self._branch_exists(branch):
            self.git.branch(branch, base).wait()

    def delete_branch(self, branch, force):
        if self._branch_exists(branch, local_only=True):
            if self.current_branch == branch:
                self.git.checkout(self.branch).wait()
            try:
                delete_flag = '-D' if force else '-d'
                self.git.branch(delete_flag, branch).wait()
            except sh.ErrorReturnCode:
                ctx.logger.error('Failed deleting branch {0}.'.format(branch))

    def branch_exists(self, branch):
        return self._branch_exists(branch)

    @property
    def location(self):
        return path(self.properties['location']).expanduser()

    @property
    def name(self):
        return self.properties['name']

    @property
    def repo_location(self):
        return self.location / self.name

    @property
    def organization(self):
        return self.properties['organization']

    @property
    def branch(self):
        return self.properties['branch']

    @property
    def clone_method(self):
        return self.properties['clone_method']

    @property
    def type(self):
        return self.properties['repo_type']

    @property
    def git_config(self):
        return self.properties['git_config']

    @property
    def git_prompt_paths(self):
        return [path(p) for p in self.properties['git_prompt_paths']]

    @property
    def git_version(self):
        return self.runtime_properties['git_version']

    @git_version.setter
    def git_version(self, value):
        self.runtime_properties['git_version'] = value

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

    @property
    def properties(self):
        return ctx.node.properties

    @property
    def runtime_properties(self):
        return ctx.instance.runtime_properties

    @property
    def versions_repo_location(self):
        with open(ctx._endpoint.storage._payload_path) as f:
            return path(json.load(f)['versions_repo_location'])

    @versions_repo_location.setter
    def versions_repo_location(self, value):
        with ctx._endpoint.storage.payload() as payload:
            current_value = payload.get('versions_repo_location')
            if current_value and current_value != value:
                raise exceptions.NonRecoverableError(
                    'only one repository can be marked with "versions" type')
            payload['versions_repo_location'] = value

    @property
    def active_feature(self):
        with open(ctx._endpoint.storage._payload_path) as f:
            active_feature = json.load(f).get('active_feature')
        if not active_feature:
            return Feature({})
        branches = {}
        features_file = path(self.properties['features_file'])
        if features_file.exists():
            branches = yaml.safe_load(features_file.text()) or {}
        if not branches:
            return Feature({})
        name = active_feature
        active_feature = Feature(branches.get(active_feature))
        active_feature.name = name
        return active_feature

    def _git(self, log_out, repo_location=None):
        repo_location = repo_location or self.repo_location
        git = sh.git
        if log_out:
            git = bake(git)
        return git.bake(
            '--no-pager',
            '--git-dir', repo_location / '.git',
            '--work-tree', repo_location)

    def validate_active_feature(self):
        active_feature = self.active_feature
        current_branch = self.current_branch
        if not active_feature.branch:
            return False
        if active_feature.branch != current_branch:
            ctx.logger.warn(
                'Current branch: "{0}" does not match the active feature '
                'branch :{1}'.format(current_branch, active_feature))
            return False
        return True

    def _branch_exists(self, branch, local_only=False):
        branch_exists = self.git_output.bake(
                'show-ref', verify=True, quiet=True)
        refs = ['refs/heads']
        if not local_only:
            refs.append('refs/remotes/origin')
        for ref in refs:
            try:
                branch_exists('{0}/{1}'.format(ref, branch))
            except sh.ErrorReturnCode:
                pass
            else:
                return True
        return False

    def _fix_branch_name(self, branch):
        if not branch.startswith('.'):
            return branch
        if self.type not in ['core', 'plugin']:
            return branch
        template = '3{}' if self.type == 'core' else '1{}'
        return template.format(branch)

    def _read_versions_file(self, versions_branch):
        repo_git = self._git(
            log_out=False,
            repo_location=self.versions_repo_location)
        try:
            raw_versions = repo_git.show(
                '{}:versions.yaml'.format(versions_branch)).stdout.strip()
        except sh.ErrorReturnCode:
            raw_versions = repo_git.show(
                'origin/{}:versions.yaml'.format(
                    versions_branch)).stdout.strip()
        versions = yaml.safe_load(raw_versions)
        return versions.get('components', {})
repo = GitRepo()


class Hub(object):

    def ci_status(self):
        if not repo.validate_active_feature():
            return
        try:
            self.hub('ci-status', '-v').wait()
        except sh.ErrorReturnCode:
            pass

    def compare(self):
        if not repo.validate_active_feature():
            return
        url = self.hub_output.compare(
            '-u', '-b', repo.active_feature.base).stdout.strip()
        import webbrowser
        webbrowser.open(url)

    def pull_request(self, message, file):
        if not repo.validate_active_feature():
            return
        if message and file:
            raise exceptions.NonRecoverableError(
                'You cannot specify both a message and a file. Pick one!')
        command = self.hub.bake('pull-request', '-b', repo.active_feature.base,
                                '-o')
        if message:
            command = command.bake('-m', message)
        elif file:
            command = command.bake('-F', file)
        else:
            message = repo.active_feature.branch
            command = command.bake('-m', message)
        try:
            command()
        except sh.ErrorReturnCode:
            pass

    @property
    def hub(self):
        return self._hub(log_out=True)

    @property
    def hub_output(self):
        return self._hub(log_out=False)

    @staticmethod
    def _hub(log_out):
        repo_location = repo.repo_location
        try:
            hub = sh.hub
        except sh.CommandNotFound:
            raise exceptions.NonRecoverableError(
                'hub must be installed to use this command.')
        if log_out:
            hub = bake(hub)
        env = os.environ.copy()
        env.update({
            'GIT_WORK_TREE': repo_location,
            'GIT_DIR': repo_location / '.git'
        })
        return hub.bake(_env=env)
hub = Hub()


@workflow
def check_branch_exists(branch, **_):
    repos = []
    for instance in workflow_ctx.node_instances:
        if instance.node.type != 'git_repo':
            continue
        exists = instance.execute_operation('git.branch_exists', kwargs={
            'branch': branch
        }).get()
        if exists:
            repos.append(instance.node.id[:-len('-repo')])
    return repos


class Feature(dict):

    def __init__(self, initial):
        self.update(initial)

    @property
    def repos(self):
        return self.get('repos')

    @property
    def branch(self):
        repos = self.repos
        if not repos:
            return None
        elif isinstance(repos, dict):
            return repos.get(repo.name)
        elif isinstance(repos, list):
            if repo.name in repos:
                return self.get('branch')
            else:
                return None
        else:
            raise exceptions.NonRecoverableError('Invalid repos: {}'
                                                 .format(repos))

    @property
    def name(self):
        return self.get('name')

    @name.setter
    def name(self, value):
        self['name'] = value

    @property
    def base(self):
        return self.get('base', 'master')


def func(repo_method):
    @operation
    def wrapper(**kwargs):
        kwargs.pop('ctx', None)
        try:
            method = getattr(repo, repo_method)
        except AttributeError:
            method = getattr(hub, repo_method)
        return method(**kwargs)
    return wrapper

for method in ['clone', 'configure', 'pull', 'status', 'checkout', 'reset',
               'rebase', 'squash', 'diff', 'create_branch', 'branch_exists',
               'delete_branch', 'ci_status', 'compare', 'pull_request']:
    globals()[method] = func(method)
