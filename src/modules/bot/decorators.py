"""Decorators for bot commands and message handlers"""


def message_handler(*args, **kwargs):
    # noinspection PyProtectedMember
    def wrapper(func):
        if not hasattr(func, '_handlers'):
            func._handlers = []
        func._handlers.append(('message', args, kwargs))
        return func
    return wrapper


def callback_query_handler(*args, **kwargs):
    # noinspection PyProtectedMember
    def wrapper(func):
        if not hasattr(func, '_handlers'):
            func._handlers = []
        func._handlers.append(('callback_query', args, kwargs))
        return func
    return wrapper
