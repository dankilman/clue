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

import argparse
import json
from contextlib import contextmanager

import argh
import colors
import yaml
from path import path

from clash import ctx


def ls():
    active_feature = features.active_feature
    for name, feature in features.load().items():
        _print_feature(name, feature, active_feature)


def _print_feature(name, feature, active_feature):
    indicator = '*' if name == active_feature else ' '
    print '{} {}:'.format(colors.red(indicator),
                          colors.magenta(name))
    indent = ' ' * 4
    branch = feature.get('branch')
    if branch:
        print '{}branch: {}'.format(indent, colors.green(branch))
    base = feature.get('base')
    if base:
        print '{}base: {}'.format(indent, colors.green(base))
    repos = feature.get('repos')
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


def create(name, branch, base):
    git_branch_exists = _command(workflow='check_branch_exists',
                                 parameters={'branch': branch})
    repos = sorted(_call(git_branch_exists))
    with features.update_feature(name) as feature:
        feature.update({
            'branch': branch,
            'repos': repos
        })
        if base:
            feature['base'] = base
    features.active_feature = name
    _print_feature(name, feature, active_feature=name)
    checkout(name)


def sync_repos(feature_name):
    feature_name = feature_name or features.active_feature
    if not feature_name:
        raise argh.CommandError('No feature is currently active.')
    if not features.exists(feature_name):
        raise argh.CommandError('No such feature: {}'.format(feature_name))
    branch = features.load()[feature_name]['branch']
    git_branch_exists = _command(workflow='check_branch_exists',
                                 parameters={'branch': branch})
    repos = sorted(_call(git_branch_exists))
    with features.update_feature(feature_name) as feature:
        feature.update({
            'repos': repos,
        })


def finish(feature_name):
    feature_name = feature_name or features.active_feature
    if not feature_name:
        raise argh.CommandError('No feature is currently active.')
    if not features.exists(feature_name):
        raise argh.CommandError('No such feature: {}'.format(feature_name))
    repos = features.load()[feature_name].get('repos', [])
    for repo in repos:
        try:
            remove_repo(repo, feature_name, force=False)
        except RuntimeError as e:
            print str(e), 'Skipping.'
    with features.update() as _features:
        _features.pop(feature_name, None)
    features.active_feature = None


def deactivate():
    features.active_feature = None
    _call(ctx.user_commands['git.checkout'], branch='default')


def checkout(name):
    feature = features.load().get(name)
    if feature:
        features.active_feature = name
    else:
        raise argh.CommandError('No such feature: {}'.format(name))
    _call(ctx.user_commands['git.checkout'], branch=name)


def add_repo(repo, feature_name):
    feature_name = feature_name or features.active_feature
    if not feature_name:
        raise argh.CommandError('No feature is currently active.')
    if not features.exists(feature_name):
        raise argh.CommandError('No such feature: {}'.format(feature_name))
    with features.update_feature(feature_name) as feature:
        branch = feature['branch']
        base = feature.get('base', 'master')
        repos = feature.get('repos', [])
        if repo not in repos:
            repos.append(repo)
        feature['repos'] = repos
    _call(_git_command(operation='git.create_branch',
                       repo=repo,
                       branch=branch,
                       base=base))
    _call(_git_command(operation='git.checkout',
                       repo=repo,
                       branch=feature_name))


def remove_repo(repo, feature_name, force):
    feature_name = feature_name or features.active_feature
    if not feature_name:
        raise argh.CommandError('No feature is currently active.')
    if not features.exists(feature_name):
        raise argh.CommandError('No such feature: {}'.format(feature_name))
    branch = features.load()[feature_name]['branch']
    _call(_git_command(operation='git.delete_branch',
                       repo=repo,
                       branch=branch,
                       force=force))
    with features.update_feature(feature_name) as feature:
        repos = feature.get('repos', [])
        if repo in repos:
            repos.remove(repo)
        feature['repos'] = repos


class Features(object):

    @property
    def path(self):
        return path(ctx.user_config.inputs['features_file'])

    def load(self):
        if not self.path.exists():
            return {}
        return yaml.safe_load(self.path.text()) or {}

    def save(self, value):
        self.path.write_text(yaml.safe_dump(value, default_flow_style=False))

    @contextmanager
    def update(self):
        content = self.load()
        yield content
        self.save(content)

    def exists(self, name):
        return name in self.load()

    @contextmanager
    def update_feature(self, name):
        with self.update() as content:
            feature = content.get(name, {})
            yield feature
            content[name] = feature

    @property
    def active_feature(self):
        with open(ctx.env.storage._payload_path) as f:
            return json.load(f).get('active_feature')

    @active_feature.setter
    def active_feature(self, value):
        with ctx.env.storage.payload() as payload:
            payload['active_feature'] = value
features = Features()


def _git_command(operation, repo, **kwargs):
    return _command(
        workflow='execute_operation',
        parameters={
            'operation': operation,
            'operation_kwargs': kwargs,
            'type_names': ['git_repo'],
            'node_ids': ['{}-repo'.format(repo)]
        },
        event_cls='clue.output:NamedNodeEvent')


def _command(workflow, parameters=None, event_cls=None):
    parameters = parameters or {}
    command = {
        'workflow': workflow,
        'parameters': parameters,
    }
    if event_cls:
        command['event_cls'] = event_cls
    return ctx._parse_command('generated', command)


def _call(command, **kwargs):
    if 'verbose' not in kwargs:
        kwargs['verbose'] = False
    return command(argparse.Namespace(**kwargs))
