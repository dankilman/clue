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
        '--git-dir', path(repo_location) / '.git',
        '--work-tree', repo_location)


@operation
def clone(location, organization, repo, branch, **_):
    git = bake(sh.git)
    location = os.path.expanduser(location)
    repo_location = os.path.join(location, repo)
    ctx.instance.runtime_properties['repo_location'] = repo_location
    if os.path.isdir(repo_location):
        return
    git.clone('git@github.com:{}/{}.git'.format(organization, repo),
              repo_location,
              '-b', branch).wait()


@operation
def configure(commit_msg_resource_path, git_config, **_):
    repo_location = path(ctx.instance.runtime_properties['repo_location'])

    # configure commit-msg hook
    commit_msg_hook_path = repo_location / '.git' / 'hooks' / 'commit-msg'
    if commit_msg_hook_path.exists():
        ctx.logger.warn('{} already exits, skipping hook installation.'
                        .format(commit_msg_hook_path))
    else:
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
    git.pull(prune=True, tags=True).wait()


@operation
def status(**_):
    git = _git()
    git('rev-parse', '--abbrev-ref', 'HEAD').wait()
    git.status(s=True).wait()


@operation
def checkout(repo_type, branch, **_):
    git = _git()
    branches_file_path = os.path.expanduser(branch)
    if os.path.exists(branches_file_path):
        with open(branches_file_path) as f:
            branches = yaml.safe_load(f.read())
        name = ctx.node.properties['name']
        if name not in branches:
            return
        branch = branches[name]
    elif repo_type == 'misc':
        return
    elif repo_type not in ['core', 'plugin']:
        raise exceptions.NonRecoverableError('Unhandled repo type: {}'
                                             .format(repo_type))
    elif not branch:
        raise exceptions.NonRecoverableError('Branch is not defined')
    elif branch.startswith('.'):
        template = '3{}' if repo_type == 'core' else '1{}'
        branch = template.format(branch)
    try:
        git.checkout(branch).wait()
    except sh.ErrorReturnCode:
        ctx.logger.error('Could not checkout branch {0}'.format(branch))
