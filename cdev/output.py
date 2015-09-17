import colors

from workflowcmd.output import Event


class GitStatusEvent(object):

    @staticmethod
    def factory(env, verbose):
        class GitStatusEventImpl(Event):

            def __str__(self):
                if (not verbose and self.level and self.level.lower() == 'info'
                        and self.node_name):
                    node = env.storage.get_node(self.node_name)
                    repo = node.properties['name']
                    repo = colors.green('{0:<30}'.format(repo))
                    return ' {0}| {1}'.format(repo, self.message)
                else:
                    return super(GitStatusEventImpl, self).__str__()
        return GitStatusEventImpl


class NoseEvent(object):

    @staticmethod
    def factory(env, verbose):
        class NoseEventImpl(Event):

            def __str__(self):
                if not verbose:
                    return self.message
                else:
                    return super(NoseEventImpl, self).__str__()
        return NoseEventImpl