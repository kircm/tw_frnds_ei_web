import os
from os.path import exists
from os.path import isfile
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from .models import Task
from .view_decorators import requires_auth
from .view_decorators import requires_tw_context
from .view_helpers import TwContextGetter
from .view_helpers import authenticate_app
from .view_helpers import create_task_for_user
from .view_helpers import logout_user
from .view_helpers import process_tw_oauth_callback_request
from .view_helpers import redirect_to_error_view
from .view_helpers import resolve_file_name_for_import
from .view_helpers import resolve_screen_name_for_export
from .view_helpers import retrieve_task
from .view_helpers import retrieve_tasks_for_user
from .view_helpers import validate_user_file_path


class AuthOkView(TemplateView):
    template_name = "tfei/auth-ok.html"

    @requires_auth
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ExportView(TemplateView):
    template_name = "tfei/export.html"

    @requires_auth
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ExportActionView(RedirectView):
    redirect_url = None

    @requires_auth
    def post(self, request, *args, **kwargs):
        ok, task_par_screen_name, err_msg_for_user = resolve_screen_name_for_export(request)
        if ok:
            self.redirect_url = create_task_for_user(request,
                                                     Task.TaskType.EXPORT.name,
                                                     "export_ok",
                                                     par_exp_screen_name=task_par_screen_name)
        else:
            self.redirect_url = redirect_to_error_view(request, err_msg_for_user)
        return super().post(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url


class ExportOkView(TemplateView):
    template_name = "tfei/export-ok.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ImportView(TemplateView):
    template_name = "tfei/import.html"

    @requires_auth
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ImportActionView(RedirectView):
    redirect_url = None

    @requires_auth
    def post(self, request, *args, **kwargs):
        ok, task_par_f_name, err_msg_for_user = resolve_file_name_for_import(request)
        if ok:
            self.redirect_url = create_task_for_user(request,
                                                     Task.TaskType.IMPORT.name,
                                                     "import_ok",
                                                     task_par_f_name=task_par_f_name)
        else:
            self.redirect_url = redirect_to_error_view(request, err_msg_for_user)
        return super().post(self, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return self.redirect_url


class ImportOkView(TemplateView):
    template_name = "tfei/import-ok.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class MyTasksView(TemplateView):
    template_name = "tfei/my-tasks.html"

    @requires_auth
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @requires_tw_context
    def get_context_data(self, **kwargs):
        context = {}
        task_data = retrieve_tasks_for_user(self.request)
        if task_data:
            context.update({'task_context': task_data})
        else:
            messages.warning(self.request, "There are no tasks")
        return context


class DownloadView(View):
    @requires_auth
    def get(self, request, *args, **kwargs):
        tw_context = TwContextGetter(request).get_tw_context()
        user_screen_name = tw_context['user_screen_name']
        user_id = tw_context['user_id']
        task_id = kwargs['task_id']
        task = retrieve_task(task_id, user_id)

        path_file = Path(task.finished_output)
        if exists(path_file) and isfile(path_file) \
                and validate_user_file_path(user_screen_name, str(path_file.absolute())):
            with open(path_file, 'r') as f:
                resp = HttpResponse(f.read(), content_type="text/csv")
                resp['Content-Disposition'] = f"attachment;filename={os.path.basename(path_file)}"
                return resp
        else:
            raise ObjectDoesNotExist()


class LogoutView(TemplateView):
    template_name = "tfei/logout.html"

    def get(self, request, *args, **kwargs):
        logout_user(request)
        return super().get(request, *args, **kwargs)


class ErrorView(TemplateView):
    template_name = "tfei/error.html"

    def get_context_data(self, **kwargs):
        if 'msg_context' in self.request.session:
            return {'msg_context': self.request.session['msg_context']}
        else:
            return {'msg_context': {'error_message': "Unknown Error! Please logout and re-authenticate"}}


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
