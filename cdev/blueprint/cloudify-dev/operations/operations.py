import tempfile
import os

import sh
import networkx as nx
import jinja2
from path import path

from cloudify import ctx
from cloudify.decorators import operation
from cloudify import exceptions


def _sh(command, logger):
    return command.bake(_out=lambda line: logger.info(line.strip()),
                        _err=lambda line: logger.warn(line.strip()))


def _git():
    repo_location = ctx.instance.runtime_properties['repo_location']
    return _sh(sh.git, ctx.logger).bake(
        '--git-dir', path(repo_location) / '.git',
        '--work-tree', repo_location)


@operation
def makedirs(location, **_):
    location = os.path.expanduser(location)
    if not os.path.isdir(location):
        os.makedirs(location)


@operation
def git_clone(location, organization, repo, branch, **_):
    git = _sh(sh.git, ctx.logger)
    location = os.path.expanduser(location)
    repo_location = os.path.join(location, repo)
    ctx.instance.runtime_properties['repo_location'] = repo_location
    if os.path.isdir(repo_location):
        return
    git.clone('git@github.com:{}/{}.git'.format(organization, repo),
              repo_location,
              '-b', branch).wait()


@operation
def git_install_commit_msg_hook(resource_path, **_):
    repo_location = path(ctx.instance.runtime_properties['repo_location'])
    commit_msg_hook_path = repo_location / '.git' / 'hooks' / 'commit-msg'
    if commit_msg_hook_path.exists():
        ctx.logger.warn('{} already exits, skipping hook installation.'
                        .format(commit_msg_hook_path))
    commit_msg_hook = ctx.get_resource(resource_path)
    with open(commit_msg_hook_path, 'w') as f:
        f.write(commit_msg_hook)
    os.chmod(commit_msg_hook_path, 0755)


@operation
def git_pull(**_):
    git = _git()
    git.pull(prune=True, tags=True).wait()


@operation
def git_status(**_):
    git = _git()
    git('rev-parse', '--abbrev-ref', 'HEAD').wait()
    git.status(s=True).wait()


@operation
def git_checkout(repo_type, branch, **_):
    git = _git()
    if repo_type == 'misc':
        return
    if repo_type not in ['core', 'plugin']:
        raise exceptions.NonRecoverableError('Unhandled repo type: {}'
                                             .format(repo_type))
    if not branch:
        raise exceptions.NonRecoverableError('Branch is not defined')
    if branch.startswith('.'):
        template = '3{}' if repo_type == 'core' else '1{}'
        branch = template.format(branch)
    git.checkout(branch)


@operation
def configure_python_package_path(repo_location, base_package_path, **_):
    package_path = os.path.join(repo_location, base_package_path)
    ctx.source.instance.runtime_properties['package_path'] = package_path


@operation
def configure_virtualenv_location(virtualenv_location, **_):
    ctx.source.instance.runtime_properties[
        'virtualenv_location'] = virtualenv_location


@operation
def configure_package_dependency(target_package_path, **_):
    _add_requierment(target_package_path, ctx.source.instance)


@operation
def add_self_requirement(package_path, **_):
    _add_requierment(package_path, ctx.instance)


@operation
def add_additional_requirements(
        requirements_path,
        requirements, **_):
    raw_requirements = ctx.get_resource(requirements_path)
    for req in raw_requirements.splitlines():
        req = req.strip()
        if not req or req.startswith('#'):
            continue
        requirements.append(req)
    ctx.instance.runtime_properties['requirements'] = requirements


def _add_requierment(package_path, instance):
    requirements = instance.runtime_properties.get('requirements', [])
    requirement = '-e {}'.format(package_path)
    if requirement not in requirements:
        requirements.append(requirement)
    instance.runtime_properties['requirements'] = requirements


@operation
def pip_install(virtualenv_location, package_path, **_):
    pip = _sh(sh.Command(os.path.join(virtualenv_location, 'bin', 'pip')),
              ctx.logger)
    pip.install(e=package_path).wait()


@operation
def install_packages(**_):
    package_node_instance_ids = ctx.capabilities.get_all().keys()
    package_node_instances = [
        ctx._endpoint.storage.get_node_instance(instance_id)
        for instance_id in package_node_instance_ids]
    package_node_instances = [
        instance for instance in package_node_instances
        if 'virtualenv_location' in instance.runtime_properties]
    virtualenvs = set((instance.runtime_properties['virtualenv_location']
                       for instance in package_node_instances))

    for virtualenv_location in virtualenvs:
        pip = _sh(sh.Command(os.path.join(virtualenv_location, 'bin', 'pip')),
                  ctx.logger)
        virutalenv_package_instances = [
            instance for instance in package_node_instances
            if instance.runtime_properties[
                'virtualenv_location'] == virtualenv_location]
        graph = nx.DiGraph()
        for instance in virutalenv_package_instances:
            graph.add_node(instance.id)
            for relationship in instance.relationships:
                graph.add_edge(instance.id, relationship['target_id'])
        topological_sort = nx.topological_sort(graph.reverse())
        requirements = []
        for instance_id in topological_sort:
            instance = ctx._endpoint.storage.get_node_instance(instance_id)
            for requirement in instance.runtime_properties.get('requirements',
                                                               []):
                if requirement not in requirements:
                    requirements.append(requirement)
        requirements_file = tempfile.mktemp(prefix='requirements-',
                                            suffix='.txt')
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(requirements))
        pip.install(requirement=requirements_file).wait()


@operation
def process_postactivate(
        virtualenv_location,
        resource_path,
        repositories_dir,
        register_python_argcomplete,
        **_):
    repositories_dir = os.path.expanduser(repositories_dir)
    template = jinja2.Template(ctx.get_resource(resource_path))
    variables = dict(
        repositories_dir=repositories_dir,
        register_python_argcomplete=register_python_argcomplete)
    with open(path(virtualenv_location) / 'bin' / 'postactivate', 'w') as f:
        f.write(template.render(**variables))
