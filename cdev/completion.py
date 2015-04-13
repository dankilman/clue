import workflowcmd


class PackageCompleter(workflowcmd.WorkflowCmdCompleter):

    def complete(self, env, prefix, **kwargs):
        nodes = env.storage.get_nodes()
        return (n.id for n in nodes
                if n.type == 'python_package' and
                n.id.startswith(prefix))
