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

from path import path

from cloudify import ctx
from cloudify import exceptions
from cloudify.decorators import operation


@operation
def create_idea_project(virtualenv_name, **_):
    project_dir, repo_paths, package_paths, resource_dirs = _extract_dirs()
    if not project_dir:
        ctx.logger.info('No project dir configured.')
        return
    project_dir = path(project_dir)
    idea_dir = project_dir / '.idea'
    name_file = idea_dir / '.name'
    project_iml = idea_dir / '{}.iml'.format(project_dir.basename())
    misc_xml = idea_dir / 'misc.xml'
    modules_xml = idea_dir / 'modules.xml'
    vcs_xml = idea_dir / 'vcs.xml'
    module_paths = []
    for resource_dir in resource_dirs:
        if resource_dir.endswith('/'):
            resource_dir = resource_dir[:-1]
        resource_dir = path(resource_dir)
        iml_path = resource_dir / '{}.iml'.format(resource_dir.basename())
        module_paths.append(iml_path)
        if not iml_path.exists():
            ctx.logger.info('Adding resource module: {}'.format(iml_path))
            ctx.download_resource_and_render(
                resource_path='resources/idea/module.xml',
                target_path=iml_path,
                template_variables={'module_type': 'WEB_MODULE'})
    for package_path in package_paths:
        if package_path.endswith('/'):
            package_path = package_path[:-1]
        package_path = path(package_path)
        iml_path = package_path / '{}.iml'.format(package_path.basename())
        module_paths.append(iml_path)
        if not iml_path.exists():
            ctx.logger.info('Adding python module: {}'.format(iml_path))
            ctx.download_resource_and_render(
                resource_path='resources/idea/module.xml',
                target_path=iml_path,
                template_variables={'module_type': 'PYTHON_MODULE'})
    if not idea_dir.exists():
        idea_dir.mkdir_p()
    if not name_file.exists():
        name_file.write_text(virtualenv_name)
    if not project_iml.exists():
        ctx.download_resource_and_render(
            resource_path='resources/idea/module.xml',
            target_path=project_iml,
            template_variables={'module_type': 'JAVA_MODULE'})
    if not misc_xml.exists():
        ctx.download_resource_and_render(
            resource_path='resources/idea/misc.xml',
            target_path=misc_xml,
            template_variables={'virtualenv_name': virtualenv_name})
    if not modules_xml.exists():
        ctx.download_resource_and_render(
            resource_path='resources/idea/modules.xml',
            target_path=modules_xml,
            template_variables={'module_paths': module_paths})
    if not vcs_xml.exists():
        ctx.download_resource_and_render(
            resource_path='resources/idea/vcs.xml',
            target_path=vcs_xml,
            template_variables={'repo_paths': repo_paths})


def _extract_dirs():
    project_dir = None
    repo_paths = []
    package_paths = []
    resource_paths = []
    for rel in ctx.instance.relationships:
        node = rel.target.node
        instance = rel.target.instance
        props = node.properties
        runtime_props = instance.runtime_properties
        if node.type == 'git_repo':
            repo_location = runtime_props['repo_location']
            repo_paths.append(repo_location)
            if props['project_dir'] is True:
                if project_dir:
                    raise exceptions.NonRecoverableError(
                            'Cannot configure more than one project dir')
                project_dir = repo_location
            resources = props['resources'] or []
            if resources is True:
                resources = ['']
            repo_location = path(repo_location)
            for resource_path in resources:
                resource_paths.append(repo_location / resource_path)
        elif node.type == 'python_package':
            package_paths.append(runtime_props['package_path'])
    return project_dir, repo_paths, package_paths, resource_paths
