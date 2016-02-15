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

import colors
import yaml
from clash import ctx
from path import path


def branch():
    branches_yaml_path = path(ctx.user_config.inputs['branches_file'])
    branches_yaml = yaml.safe_load(branches_yaml_path.text())
    for instance in ctx.env.storage.get_node_instances():
        active_branch_set = instance.runtime_properties.get(
            'active_branch_set')
        if active_branch_set:
            active_branch_set = active_branch_set['name']
            break
    else:
        active_branch_set = None
    for name, branch_set in branches_yaml.items():
        indicator = '*' if name == active_branch_set else ' '
        print '{} {}:'.format(colors.red(indicator),
                              colors.magenta(name))
        indent = ' ' * 4
        branch = branch_set.get('branch')
        if branch:
            print '{}branch: {}'.format(indent, colors.green(branch))
        base = branch_set.get('base')
        if base:
            print '{}base: {}'.format(indent, colors.green(base))
        repos = branch_set.get('repos')
        if repos:
            print '{}repos:'.format(indent)
            if isinstance(repos, list):
                for repo in repos:
                    print '{}- {}'.format(indent, colors.green(repo))
            else:
                for repo, branch in repos.items():
                    print '{}  {}: {}'.format(indent,
                                              colors.green(repo),
                                              colors.green(branch))
        print
