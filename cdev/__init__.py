from workflowcmd.config import load


def main():
    load(package='cdev',
         config_path='blueprint/workflowcmd.yaml',
         storage_dir='~/work/cdev')
