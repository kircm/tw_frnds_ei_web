from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView

from .view_decorators import requires_tw_context
from .view_helpers import authenticate_app
from .view_helpers import process_tw_oauth_callback_request


class IndexView(TemplateView):
    template_name = "tfei/index.html"

    def get_context_data(self, **kwargs):
        return {}


class MainMenuView(TemplateView):
    template_name = "tfei/main-menu.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ExportView(TemplateView):
    template_name = "tfei/export.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ImportView(TemplateView):
    template_name = "tfei/import.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class LogoutView(TemplateView):
    template_name = "tfei/logout.html"

    def get(self, request, *args, **kwargs):
        self.request.session.flush()
        return super().get(request, *args, **kwargs)


class ErrorView(TemplateView):
    template_name = "tfei/auth-nk.html"

    def get_context_data(self, **kwargs):
        context = {'msg_context': self.request.session['msg_context']}
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
        process_tw_oauth_callback_request(request, request.GET)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        process_tw_oauth_callback_request(request, request.POST)
        return super().post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url
