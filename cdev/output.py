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

from workflowcmd.output import Event


class GitStatusEvent(object):

    @staticmethod
    def factory(env, verbose):
        class GitStatusEventImpl(Event):
            def __str__(self):
                if (not verbose and self.level and
                        self.level.lower() == 'info' and
                        self.node_name):
                    node = env.storage.get_node(self.node_name)
                    repo = node.properties['name']
                    repo = colors.green('{0:<30}'.format(repo))
                    return ' {0}| {1}'.format(repo, self.message)
                else:
                    return super(GitStatusEventImpl, self).__str__()
        return GitStatusEventImpl


class NoseEvent(object):

    @staticmethod
    def factory(env, verbose):
        class NoseEventImpl(Event):
            def __str__(self):
                if not verbose:
                    return self.message
                else:
                    return super(NoseEventImpl, self).__str__()
        return NoseEventImpl
