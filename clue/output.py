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

from clash.output import Event


class NamedNodeEvent(object):

    @staticmethod
    def factory(env, verbose, command):
        max_len = 0
        git_command = command.get('parameters', {}).get(
            'operation').startswith('git.')
        node_type = 'git_repo' if git_command else 'python_package'
        for node in env.storage.get_nodes():
            if node.type == node_type:
                max_len = max(max_len, len(node.properties['name']))
        formatting = '{0:<' + str(max_len + 1) + '}'

        class NamedNodeEventImpl(Event):
            def __str__(self):
                if (not verbose and self.level and
                        self.level.lower() in ['info', 'warning'] and
                        self.node_name):
                    node = env.storage.get_node(self.node_name)
                    name = node.properties['name']
                    name = colors.green(formatting.format(name))
                    return ' {0}| {1}'.format(name, self.message)
                else:
                    return super(NamedNodeEventImpl, self).__str__()
        return NamedNodeEventImpl


class NoseEvent(object):

    @staticmethod
    def factory(env, verbose, command):
        class NoseEventImpl(Event):
            def __str__(self):
                if not verbose:
                    return self.message
                else:
                    return super(NoseEventImpl, self).__str__()
        return NoseEventImpl
