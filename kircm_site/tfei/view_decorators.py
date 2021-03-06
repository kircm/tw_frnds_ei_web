from django.conf import settings
from django.core.exceptions import PermissionDenied


def requires_auth(get_fun):
    def wrapper(*args, **kwargs):
        view_instance = args[0]
        sess = view_instance.request.session

        if 'tw_context' in sess or 'd_auth' in settings.D_AUTH:
            return get_fun(*args, **kwargs)
        else:
            raise_permission_denied(sess)

    return wrapper


def requires_tw_context(get_context_fun):
    def wrapper(*args, **kwargs):
        view_instance = args[0]
        sess = view_instance.request.session
        context = get_context_fun(*args, **kwargs) or {}

        if 'tw_context' in sess:
            context.update({'tw_context': sess['tw_context']})
        elif 'd_auth' in settings.D_AUTH:
            context.update({'tw_context': settings.D_AUTH['d_auth']})
        else:
            raise_permission_denied(sess)
        return context

    return wrapper


def raise_permission_denied(sess):
    msg = "403 Not Authorized"
    sess['msg_context'] = {'error_message': msg}
    raise PermissionDenied
