import os
import json

import sh
from path import path

from cloudify import ctx
from cloudify.decorators import operation
from cloudify import exceptions

from common import bake

@operation
def makedirs(location, **_):
    location = os.path.expanduser(location)
    if not os.path.isdir(location):
        os.makedirs(location)


@operation
def nose_run(virtualenv_location, test_path, **_):
    nose = bake(sh.Command(os.path.join(virtualenv_location, 'bin',
                                        'nosetests')))
    try:
        nose(test_path,
             nocapture=True,
             nologcapture=True,
             verbose=True).wait()
    except:
        raise exceptions.NonRecoverableError()


@operation
def configure_docs_getcloudify_source(docs_getcloudify_repo_location, **_):
    repo_location = path(
        ctx.source.instance.runtime_properties['repo_location'])
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
            npm = bake(sh.npm)
            npm.install().wait()
        if not bower_components_path.exists():
            bower = bake(sh.bower)
            bower.install().wait()
