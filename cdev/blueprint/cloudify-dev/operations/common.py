from cloudify import ctx


def bake(command):
    logger = ctx.logger
    return command.bake(_out=lambda line: logger.info(line.strip()),
                        _err=lambda line: logger.warn(line.strip()))
