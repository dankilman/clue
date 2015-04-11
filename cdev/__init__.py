import workflowcmd


def main():
    workflowcmd.dispatch(
        package='cdev',
        config_path='blueprint/workflowcmd.yaml',
        blueprint_path='blueprint/cloudify-dev/blueprint.yaml',
        storage_dir='~/work/cdev')
