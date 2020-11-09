from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView

from .models import Task
from .view_decorators import requires_auth
from .view_decorators import requires_tw_context
from .view_helpers import authenticate_app
from .view_helpers import create_task_for_user
from .view_helpers import logout_user
from .view_helpers import process_tw_oauth_callback_request


class MainMenuView(TemplateView):
    template_name = "tfei/main-menu.html"

    @requires_auth
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ExportView(RedirectView):
    redirect_url = None

    @requires_auth
    def get(self, request, *args, **kwargs):
        self.redirect_url = create_task_for_user(request, Task.TaskType.EXPORT.name, "export_ok")
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url


class ExportOkView(TemplateView):
    template_name = "tfei/export-ok.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ImportView(RedirectView):
    redirect_url = None

    @requires_auth
    def get(self, request, *args, **kwargs):
        self.redirect_url = create_task_for_user(request, Task.TaskType.IMPORT.name, "import_ok")
        return super().get(self, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url


class ImportOkView(TemplateView):
    template_name = "tfei/import-ok.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class LogoutView(TemplateView):
    template_name = "tfei/logout.html"

    def get(self, request, *args, **kwargs):
        logout_user(request)
        return super().get(request, *args, **kwargs)


class ErrorView(TemplateView):
    template_name = "tfei/error.html"

    def get_context_data(self, **kwargs):
        if 'msg_context' in self.request.session:
            context = {'msg_context': self.request.session['msg_context']}
        else:
            context = {'msg_context': {'error_message': "Unknown Error! Please logout and re-authenticate"}}
        return context


class TwAuthenticateRedirectView(RedirectView):
    redirect_url = None

    def get(self, request, *args, **kwargs):
        self.redirect_url = authenticate_app(request)
        return super().get(self, request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url


class TwAuthCallbackView(RedirectView):
    absolute_url_builder = None
    redirect_url = None

    def get(self, request, *args, **kwargs):
        self.redirect_url = process_tw_oauth_callback_request(request, request.GET)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.redirect_url = process_tw_oauth_callback_request(request, request.POST)
        return super().post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url
