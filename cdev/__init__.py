import sys

import workflowcmd


def main():
    workflowcmd.dispatch(package=sys.modules[__name__],
                         config_path='blueprint/workflowcmd.yaml')
