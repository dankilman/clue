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

import sh
import yaml
from path import path

from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation

from common import bake


def _git():
    repo_location = ctx.instance.runtime_properties['repo_location']
    return bake(sh.git).bake(
        '--no-pager',
        '--git-dir', path(repo_location) / '.git',
        '--work-tree', repo_location)


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
    commit_msg_hook = ctx.get_resource(commit_msg_resource_path)
    with open(commit_msg_hook_path, 'w') as f:
        f.write(commit_msg_hook)
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
def status(**_):
    git = _git()
    git('rev-parse', '--abbrev-ref', 'HEAD').wait()
    git.status(s=True).wait()


@operation
def checkout(repo_type, branch, **_):
    git = _git()
    branches_file = os.path.expanduser(ctx.node.properties['branches_file'])
    branches = {}
    if os.path.exists(branches_file):
        with open(branches_file) as f:
            branches = yaml.safe_load(f)
    if branch in branches:
        branches_set = branches[branch]
        name = ctx.node.properties['name']
        if name in branches_set:
            branch = branches_set[name]
        else:
            branch = ctx.node.properties['branch']
    elif branch == 'default':
        branch = ctx.node.properties['branch']
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
    except sh.ErrorReturnCode:
        ctx.logger.error('Could not checkout branch {0}'.format(branch))


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
    template = '3{}' if repo_type == 'core' else '1{}'
    return template.format(branch)
