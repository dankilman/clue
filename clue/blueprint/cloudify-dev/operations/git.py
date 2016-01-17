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

import sh
import yaml
from path import path

from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation

from common import bake


def _git(log_out=True):
    repo_location = ctx.instance.runtime_properties['repo_location']
    git = sh.git
    if log_out:
        git = bake(git)
    return git.bake(
        '--no-pager',
        '--git-dir', path(repo_location) / '.git',
        '--work-tree', repo_location)


def _current_branch():
    git = _git(log_out=False)
    return git('rev-parse', '--abbrev-ref', 'HEAD').stdout.strip()


@operation
def clone(location, organization, repo, branch, clone_method, **_):
    git = bake(sh.git)

    location = os.path.expanduser(location)
    repo_location = os.path.join(location, repo)
    ctx.instance.runtime_properties['repo_location'] = repo_location
    ctx.instance.runtime_properties['git_version'] = sh.git(
        version=True).stdout.strip()
    if os.path.isdir(repo_location):
        return
    if clone_method == 'https':
        clone_url = 'https://github.com/{}/{}.git'.format(organization, repo)
    elif clone_method == 'ssh':
        clone_url = 'git@github.com:{}/{}.git'.format(organization, repo)
    else:
        raise exceptions.NonRecoverableError('Illegal clone method: {0}'
                                             .format(clone_method))
    git.clone(clone_url,
              repo_location,
              '-b', branch).wait()


@operation
def configure(commit_msg_resource_path, git_config, **_):
    repo_location = path(ctx.instance.runtime_properties['repo_location'])

    # configure commit-msg hook
    commit_msg_hook_path = repo_location / '.git' / 'hooks' / 'commit-msg'
    ctx.download_resource_and_render(
        commit_msg_resource_path,
        template_variables={'sys_executable': sys.executable},
        target_path=commit_msg_hook_path)
    os.chmod(commit_msg_hook_path, 0755)

    # git config
    git = _git()
    for key, value in git_config.items():
        git.config(key, value).wait()


@operation
def pull(**_):
    git = _git()
    kwargs = {
        'prune': True
    }
    git_version = ctx.instance.runtime_properties['git_version']
    if git_version >= 'git version 2.0.0':
        kwargs['tags'] = True
    git.pull(**kwargs).wait()


@operation
def status(git_prompt_paths, **_):
    git = _git()

    for git_prompt_path in git_prompt_paths:
        if os.path.exists(os.path.expanduser(git_prompt_path)):
            break
    else:
        git_prompt_path = None

    if git_prompt_path:
        repo_location = ctx.instance.runtime_properties['repo_location']
        script_path = ctx.download_resource_and_render(
            'resources/git-branch-state.sh', template_variables={
                'git_prompt_path': git_prompt_path,
                'repo_location': repo_location})
        try:
            os.chmod(script_path, 0o0755)
            script = sh.Command(script_path)
            branch_state = script().stdout.strip()
        finally:
            os.remove(script_path)
    else:
        branch_state = _current_branch()
    ctx.logger.info(branch_state)
    git.status(s=True).wait()


@operation
def checkout(repo_type, branch, **_):
    git = _git()
    default_branch = ctx.node.properties['branch']
    branches_file = os.path.expanduser(ctx.node.properties['branches_file'])
    branches = {}
    current_branch_set = None
    if os.path.exists(branches_file):
        with open(branches_file) as f:
            branches = yaml.safe_load(f) or {}
    if branch in branches:
        branches_set = branches[branch]
        name = ctx.node.properties['name']
        if all(k in branches_set for k in ['branch', 'repos']):
            if name in branches_set['repos']:
                current_branch_set = branch
                branch = branches_set['branch']
            else:
                branch = default_branch
        else:
            if name in branches_set:
                current_branch_set = branch
                branch = branches_set[name]
            else:
                branch = default_branch
    elif branch == 'default':
        branch = default_branch
    elif repo_type == 'misc':
        return
    elif repo_type not in ['core', 'plugin']:
        raise exceptions.NonRecoverableError('Unhandled repo type: {}'
                                             .format(repo_type))
    elif not branch:
        raise exceptions.NonRecoverableError('Branch is not defined')
    elif branch.startswith('.'):
        branch = _fix_branch_name(repo_type, branch)
    try:
        git.checkout(branch).wait()
        if current_branch_set:
            ctx.instance.runtime_properties[
                'current_branch_set'] = current_branch_set
            ctx.instance.runtime_properties[
                'current_branch_set_branch'] = branch
        else:
            ctx.instance.runtime_properties.pop('current_branch_set', None)
            ctx.instance.runtime_properties.pop('current_branch_set_branch',
                                                None)
    except sh.ErrorReturnCode:
        ctx.logger.error('Could not checkout branch {0}'.format(branch))


@operation
def squash(fork_point, **_):
    if not _validate_branch_set():
        return
    git = _git(log_out=False)
    merge_base = git.bake('merge-base', fork_point=True)(
        fork_point).stdout.strip()
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
    git = _git(log_out=True)
    ctx.logger.info('Squashing with merge_base: {0} and commit message: {1}'
                    .format(merge_base, commit_message))
    git.reset(merge_base, soft=True).wait()
    git.commit(message=commit_message).wait()


@operation
def reset(hard, origin, **_):
    if not _validate_branch_set():
        return
    git = _git()
    current_branch = _current_branch()
    git.reset.bake(hard=hard)('{0}/{1}'.format(origin, current_branch)).wait()


@operation
def rebase(branch, repo_type, **_):
    if not _validate_branch_set():
        return
    git = _git()
    try:
        branch = _fix_branch_name(repo_type, branch)
        git.rebase(branch).wait()
    except Exception as e:
        ctx.logger.error('Failed rebase, aborting: {0}'.format(e))
        try:
            git.rebase(abort=True).wait()
        except:
            pass


def _validate_branch_set():
    current_branch_set = ctx.instance.runtime_properties.get(
            'current_branch_set')
    current_branch_set_branch = ctx.instance.runtime_properties.get(
            'current_branch_set_branch')
    if not (current_branch_set and current_branch_set_branch):
        return False
    current_branch = _current_branch()
    if current_branch_set_branch != current_branch:
        ctx.logger.warn(
            'Current branch: "{0}" does not match current branch set: "{1}" '
            'branch "{2}"'.format(current_branch,
                                  current_branch_set,
                                  current_branch_set_branch))
        return False
    return True


@operation
def diff(repo_type, revision_range, **_):
    if repo_type not in ['core', 'plugin']:
        return
    split_range = revision_range.split('..')
    if len(split_range) != 2:
        ctx.logger.error('Invalid range supplied: {0}'.format(revision_range))
        return
    left = _fix_branch_name(repo_type, split_range[0])
    right = _fix_branch_name(repo_type, split_range[1])
    diff_range = '{0}..{1}'.format(left, right)
    try:
        git = _git()
        git.diff(diff_range).wait()
    except sh.ErrorReturnCode:
        ctx.logger.error('{0} diff failed'.format(diff_range))


def _fix_branch_name(repo_type, branch):
    if not branch.startswith('.'):
        return branch
    if repo_type not in ['core', 'plugin']:
        return branch
    template = '3{}' if repo_type == 'core' else '1{}'
    return template.format(branch)
