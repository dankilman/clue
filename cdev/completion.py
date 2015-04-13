def package_completer(env, prefix, **kwargs):
    nodes = env.storage.get_nodes()
    return (n.id for n in nodes
            if n.type == 'python_package' and
            n.id.startswith(prefix))
