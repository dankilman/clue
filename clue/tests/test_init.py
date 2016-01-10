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

import sh

from clue import tests


class TestInit(tests.BaseTest):

    def test_basic(self):
        self._test()

    def test_existing_no_reset(self):
        self._test()
        with self.assertRaises(sh.ErrorReturnCode) as c:
            self._test(skip_setup=True)
        self.assertIn('--reset to re-initialize', c.exception.stderr)

    def test_existing_reset(self):
        self._test()
        self._test(skip_setup=True, reset=True)

    def test_no_docs_no_docs_site(self):
        self._test_docs(docs=False, docs_site=False)

    def test_no_docs_yes_docs_site(self):
        self._test_docs(docs=False, docs_site=True)

    def test_yes_docs_no_docs_site(self):
        self._test_docs(docs=True, docs_site=False)

    def _test_docs(self, docs, docs_site):
        self.clue.setup(repos_dir=self.repos_dir)
        inputs = self.inputs()
        repos = {}
        if docs:
            repos['docs.getcloudify.org'] = {'python': False}
        if docs_site:
            repos['docs.getcloudify.org-site'] = {'python': False}
        inputs['repos'] = {'misc': repos}
        self.set_inputs(inputs)
        self.clue.init()
        node_templates = self.blueprint()['node_templates']
        docs_node = node_templates.get('docs.getcloudify.org-repo')
        docs_site_node = node_templates.get('docs.getcloudify.org-site-repo')
        assertion = self.assertIsNotNone if docs else self.assertIsNone
        assertion(docs_node)
        assertion = self.assertIsNotNone if docs_site else self.assertIsNone
        assertion(docs_site_node)
        if docs_site and not docs:
            self.assertEqual(1, len(docs_site_node['relationships']))

    def _test(self, reset=False, skip_setup=False):
        if not skip_setup:
            self.clue.setup(repos_dir=self.repos_dir)
        inputs = self.inputs()
        inputs['repos'] = {
            'core': {
                'cloudify-dsl-parser': {},
                'cloudify-rest-client': {},
                'cloudify-plugins-common': {
                    'python': {
                        'dependencies': [
                            'cloudify-rest-client',
                            'cloudify-dsl-parser'
                        ]
                    }
                },
                'cloudify-manager': {
                    'python': [
                        {'name': 'cloudify-rest-service',
                         'path': 'rest-service',
                         'dependencies': ['cloudify-dsl-parser']},
                        {'name': 'cloudify-workflows',
                         'path': 'workflows'}
                    ]
                },
                'cloudify-cli': {}
            },
            'plugin': {
                'cloudify-openstack-plugin': {},
                'cloudify-aws-plugin': {
                    'python': {
                        'dependencies': ['cloudify-plugins-common']
                    }
                }
            },
            'misc': {
                'docs.getcloudify.org': {
                    'python': False
                },
                'docs.getcloudify.org-site': {
                    'python': False
                },
                'claw': {
                    'properties': {
                        'organization': 'dankilman'
                    }
                }
            }
        }
        self.set_inputs(inputs)
        self.clue.init(reset=reset)
        node_templates = self.blueprint()['node_templates']
        for repo in ['cloudify-dsl-parser', 'cloudify-rest-client',
                     'cloudify-plugins-common', 'cloudify-manager',
                     'cloudify-cli', 'cloudify-openstack-plugin',
                     'cloudify-aws-plugin', 'docs.getcloudify.org',
                     'docs.getcloudify.org-site', 'claw']:
            node_template_name = '{}-repo'.format(repo)
            self.assertIn(node_template_name, node_templates)
            node_template = node_templates[node_template_name]
            self.assertEqual(node_template['type'], 'git_repo')
            relationships = node_template['relationships']
            self.assertIn({
                'target': 'repos_dir',
                'type': 'cloudify.relationships.depends_on'
            }, relationships)
            if repo == 'docs.getcloudify.org-site':
                self.assertEqual(len(relationships), 2)
                self.assertIn({
                    'target': 'docs.getcloudify.org-repo',
                    'type': 'docs_site_depends_on_docs'
                }, relationships)
            else:
                self.assertEqual(len(relationships), 1)
            properties = node_template['properties']
            self.assertEqual(properties['name'], repo)
            repo_type = properties['repo_type']
            if repo == 'cloudify-dsl-parser':
                self.assertEqual(repo_type, 'core')
            elif repo == 'cloudify-openstack-plugin':
                self.assertEqual(repo_type, 'plugin')
            elif repo == 'claw':
                self.assertEqual(repo_type, 'misc')
                self.assertEqual(properties['organization'], 'dankilman')

        package_installer = node_templates['package_installer']
        installer_relationships = package_installer['relationships']

        for package in ['cloudify-dsl-parser', 'cloudify-rest-client',
                        'cloudify-plugins-common', 'cloudify-rest-service',
                        'cloudify-workflows',
                        'cloudify-cli', 'cloudify-openstack-plugin',
                        'cloudify-aws-plugin', 'claw']:
            node_template_name = '{}-package'.format(package)
            self.assertIn(node_template_name, node_templates)
            self.assertIn({
                'target': node_template_name,
                'type': 'cloudify.relationships.depends_on'
            }, installer_relationships)
            node_template = node_templates[node_template_name]
            self.assertEqual(node_template['type'], 'python_package')
            properties = node_template['properties']
            self.assertEqual(properties['name'], package)
            if package == 'cloudify-rest-service':
                expected_path = 'rest-service'
            elif package == 'cloudify-workflows':
                expected_path = 'workflows'
            else:
                expected_path = ''
            self.assertEqual(properties['path'], expected_path)
            relationships = node_template['relationships']
            self.assertIn({
                'target': 'virtualenv',
                'type': 'package_depends_on_virtualenv'
            }, relationships)

            if package in ['cloudify-rest-service', 'cloudify-workflows']:
                expected_repo = 'cloudify-manager-repo'
            else:
                expected_repo = '{}-repo'.format(package)
            self.assertIn({
                'target': expected_repo,
                'type': 'package_depends_on_repo'
            }, relationships)

            if package in ['cloudify-aws-plugin', 'cloudify-openstack-plugin']:
                rel = {
                    'target': 'cloudify-plugins-common-package',
                    'type': 'package_depends_on_package'
                }
                self.assertIn(rel, relationships)
                self.assertEqual(1, relationships.count(rel))
                self.assertEqual(3, len(relationships))
            elif package == 'cloudify-plugins-common':
                self.assertIn({
                    'target': 'cloudify-rest-client-package',
                    'type': 'package_depends_on_package'
                }, relationships)
                self.assertIn({
                    'target': 'cloudify-dsl-parser-package',
                    'type': 'package_depends_on_package'
                }, relationships)
                self.assertEqual(4, len(relationships))
            elif package == 'cloudify-rest-service':
                self.assertIn({
                    'target': 'cloudify-dsl-parser-package',
                    'type': 'package_depends_on_package'
                }, relationships)
                self.assertEqual(3, len(relationships))
            else:
                self.assertEqual(2, len(relationships))

        docs_site = node_templates['docs.getcloudify.org-site-repo']
        relationships = docs_site['relationships']
        self.assertIn({
            'target': 'docs.getcloudify.org-repo',
            'type': 'docs_site_depends_on_docs'
        }, relationships)

        for repo in ['docs.getcloudify.org', 'docs.getcloudify.org-site']:
            self.assertIn('{}-repo'.format(repo), node_templates)
            self.assertNotIn('{}-package'.format(repo), node_templates)
