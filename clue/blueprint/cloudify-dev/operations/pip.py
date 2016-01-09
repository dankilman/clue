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
import tempfile

import sh
import networkx
from path import path

from cloudify import ctx
from cloudify.decorators import operation

from common import bake


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
    _add_requirement(target_package_path, ctx.source.instance)


@operation
def add_self_requirement(package_path, **_):
    _add_requirement(package_path, ctx.instance)


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


def _add_requirement(package_path, instance):
    requirements = instance.runtime_properties.get('requirements', [])
    requirement = '-e {}'.format(package_path)
    if requirement not in requirements:
        requirements.append(requirement)
    instance.runtime_properties['requirements'] = requirements


@operation
def install(virtualenv_location, package_path, **_):
    pip = bake(sh.Command(os.path.join(virtualenv_location, 'bin', 'pip')))
    pip.install(
        c=os.path.join(virtualenv_location, 'constraints.txt'),
        e=package_path).wait()


@operation
def install_packages(**_):
    storage = ctx._endpoint.storage
    package_node_instance_ids = ctx.capabilities.get_all().keys()
    package_node_instances = [storage.get_node_instance(instance_id)
                              for instance_id in package_node_instance_ids]
    package_node_instances = [
        instance for instance in package_node_instances
        if 'virtualenv_location' in instance.runtime_properties]
    virtualenvs = set((instance.runtime_properties['virtualenv_location']
                       for instance in package_node_instances))

    for virtualenv_location in virtualenvs:
        pip = bake(sh.Command(os.path.join(virtualenv_location, 'bin', 'pip')))
        virtualenv_package_instances = [
            instance for instance in package_node_instances
            if instance.runtime_properties[
                'virtualenv_location'] == virtualenv_location]
        graph = networkx.DiGraph()
        for instance in virtualenv_package_instances:
            graph.add_node(instance.id)
            for relationship in instance.relationships:
                graph.add_edge(instance.id, relationship['target_id'])
        topological_sort = networkx.topological_sort(graph.reverse())
        requirements = []
        for instance_id in topological_sort:
            instance = storage.get_node_instance(instance_id)
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
        git_retag_cloudify_resource_path,
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

    virtualenv_bin = path(virtualenv_location) / 'bin'

    # postactivate
    repositories_dir = os.path.expanduser(repositories_dir)
    variables = dict(
        repositories_dir=repositories_dir,
        register_python_argcomplete=register_python_argcomplete)
    ctx.download_resource_and_render(
        postactivate_resource_path,
        target_path=virtualenv_bin / 'postactivate',
        template_variables=variables)

    # git-retag-cloudify
    retag_cloudify_target_path = virtualenv_bin / 'git-retag-cloudify'
    ctx.download_resource(
        git_retag_cloudify_resource_path,
        target_path=retag_cloudify_target_path)
    os.chmod(retag_cloudify_target_path, 0755)
