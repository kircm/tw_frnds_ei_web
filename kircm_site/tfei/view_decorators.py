from django.core.exceptions import PermissionDenied
from .config_env import D_AUTH


def requires_tw_context(get_context_fun):
    def wrapper(*args, **kwargs):
        view_instance = args[0]
        sess = view_instance.request.session
        context = get_context_fun(*args, **kwargs) or {}

        if 'tw_context' in sess:
            context.update({'tw_context': sess['tw_context']})
        elif 'd_auth' in D_AUTH:
            context.update({'tw_context': D_AUTH['d_auth']})
        else:
            raise PermissionDenied
        return context

    return wrapper
