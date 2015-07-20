import tempfile
import os
import json

import sh
import networkx as nx
import jinja2
import yaml
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
def git_configure(commit_msg_resource_path, git_config, **_):
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
    git.checkout(branch).wait()


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
    pip.install(
        c=os.path.join(virtualenv_location, 'constraints.txt'),
        e=package_path).wait()


@operation
def nose_run(virtualenv_location, test_path, **_):
    nose = _sh(sh.Command(os.path.join(virtualenv_location, 'bin',
                                       'nosetests')),
               ctx.logger)
    try:
        nose(test_path,
             nocapture=True,
             nologcapture=True,
             verbose=True).wait()
    except:
        raise exceptions.NonRecoverableError()


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
        pip.install(
            requirement=requirements_file,
            c=os.path.join(virtualenv_location, 'constraints.txt')).wait()


@operation
def configure_virtualenv(
        virtualenv_location,
        constraints_resource_path,
        additional_constraints,
        postactivate_resource_path,
        repositories_dir,
        register_python_argcomplete,
        **_):

    # constraints.txt
    constraints = []
    if constraints_resource_path:
        raw_constraints = ctx.get_resource(constraints_resource_path)
        for constraint in raw_constraints.splitlines():
            constraint = constraint.strip()
            if not constraint or constraint.startswith('#'):
                continue
            constraints.append(constraint)
    constraints += additional_constraints
    constraints_path = os.path.join(
        ctx.instance.runtime_properties['virtualenv_location'],
        'constraints.txt')
    with open(constraints_path, 'w') as f:
        f.write('\n'.join(constraints))

    # postactivate
    repositories_dir = os.path.expanduser(repositories_dir)
    postactivate_template = jinja2.Template(ctx.get_resource(postactivate_resource_path))
    variables = dict(
        repositories_dir=repositories_dir,
        register_python_argcomplete=register_python_argcomplete)
    with open(path(virtualenv_location) / 'bin' / 'postactivate', 'w') as f:
        f.write(postactivate_template.render(**variables))


@operation
def configure_docs_getcloudify_source(docs_getcloudify_repo_location, **_):
    repo_location = path(ctx.source.instance.runtime_properties['repo_location'])
    dev_directory = repo_location / 'dev'
    config_path = dev_directory / 'config.json'
    node_modules_path = repo_location / 'node_modules'
    bower_components_path = repo_location / 'static' / 'bower_components'

    if not dev_directory.exists():
        dev_directory.mkdir()

    config_path.write_text(json.dumps({
        'content': {
            'root': docs_getcloudify_repo_location
        }
    }))

    with repo_location:
        if not node_modules_path.exists():
            npm = _sh(sh.npm, ctx.logger)
            npm.install().wait()
        if not bower_components_path.exists():
            bower = _sh(sh.bower, ctx.logger)
            bower.install().wait()
