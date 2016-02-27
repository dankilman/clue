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


def package_completer(env, prefix, **_):
    nodes = env.storage.get_nodes()
    suffix_len = len('-package')
    return (n.id[:-suffix_len] for n in nodes
            if n.type == 'python_package' and
            n.id.startswith(prefix))


def repo_completer(env, prefix, **_):
    nodes = env.storage.get_nodes()
    suffix_len = len('-repo')
    return (n.id[:-suffix_len] for n in nodes
            if n.type == 'git_repo' and
            n.id.startswith(prefix))


def active_feature_repo_completer(env, prefix, **_):
    import json
    with open(env.storage._payload_path) as f:
        active_feature = json.load(f).get('active_feature')
    if not active_feature:
        return []
    features = _load_features_file(env)
    active_feature = features.get(active_feature)
    if not active_feature:
        return []
    repos = active_feature.get('repos', [])
    return (repo for repo in repo_completer(env, prefix)
            if repo in repos)


def features_completer(env, prefix, **_):
    features = _load_features_file(env)
    return [k for k in features if k.startswith(prefix)]


def branches_completer(env, prefix, **_):
    versions_prefix = '::'
    if prefix.startswith(versions_prefix):
        from path import path
        from sh import git
        import json
        with open(env.storage._payload_path) as f:
            versions_repo_location = path(
                json.load(f)['versions_repo_location'])
        with versions_repo_location:
            result = git('show-ref').stdout.split('\n')
            result = ['{}{}'.format(versions_prefix,
                                    r.strip().rsplit('/', 1)[-1])
                      for r in result]
            return [r for r in result if r.startswith(prefix)]
    else:
        result = []
        if 'default'.startswith(prefix):
            result.append('default')
        return result


def _load_features_file(env):
    features_file = env.plan['inputs'].get('features_file')
    if not features_file:
        return []
    import os
    features_file = os.path.expanduser(features_file)
    if not os.path.exists(features_file):
        return []
    import yaml
    with open(features_file) as f:
        features = yaml.safe_load(f) or {}
    return features
