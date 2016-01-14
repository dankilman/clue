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


def package_completer(env, prefix, **kwargs):
    nodes = env.storage.get_nodes()
    return (n.id for n in nodes
            if n.type == 'python_package' and
            n.id.startswith(prefix))


def branches_completer(env, prefix, **kwargs):
    branches_file = env.plan['inputs'].get('branches_file')
    if not branches_file:
        return []
    import os
    branches_file = os.path.expanduser(branches_file)
    if not os.path.exists(branches_file):
        return []
    import yaml
    with open(branches_file) as f:
        branches = yaml.safe_load(f)
    result = [k for k in branches if k.startswith(prefix)]
    if 'default'.startswith(prefix):
        result.append('default')
    return result
