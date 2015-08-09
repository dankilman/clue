def package_completer(env, prefix, **kwargs):
    nodes = env.storage.get_nodes()
    return (n.id for n in nodes
            if n.type == 'python_package' and
            n.id.startswith(prefix))


def branches_completer(env, prefix, **kwargs):
    branches_dir = env.plan['inputs'].get('branches_dir')
    if not branches_dir:
        return []
    import os
    return os.listdir(os.path.expanduser(branches_dir))
