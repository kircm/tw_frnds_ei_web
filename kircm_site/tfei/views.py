import os
from os.path import exists
from os.path import isfile
from pathlib import Path

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.base import RedirectView
from django.views.generic.base import TemplateView
from django.views.generic.base import View

from .forms import ExportScreenNameForm
from .forms import ImportFileForm
from .models import Task
from .view_decorators import requires_auth
from .view_decorators import requires_tw_context
from .view_helpers import TwContextGetter
from .view_helpers import add_deserialized_output_and_details
from .view_helpers import authenticate_app
from .view_helpers import create_task_for_user
from .view_helpers import handle_upload_file
from .view_helpers import logout_user
from .view_helpers import process_tw_oauth_callback_request
from .view_helpers import redirect_to_error_view
from .view_helpers import resolve_screen_name_for_export
from .view_helpers import retrieve_task_for_user
from .view_helpers import retrieve_tasks_for_user
from .view_helpers import task_for_user_exists
from .view_helpers import validate_user_file_path


class AuthOkView(TemplateView):
    template_name = "tfei/auth-ok.html"

    @requires_auth
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ExportView(View):
    @requires_auth
    def get(self, request, *args, **kwargs):
        u = TwContextGetter(request).get_tw_context()
        user_id = u['user_id']
        task_exists, msg_context = task_for_user_exists(user_id)
        if task_exists:
            return render(request, 'tfei/export.html', {'msg_context': msg_context})
        else:
            screen_name = u['user_screen_name']
            form = ExportScreenNameForm(initial={'tw_user_to_export': screen_name})
            return render(request, 'tfei/export.html', {'form': form})

    @requires_auth
    def post(self, request, *args, **kwargs):
        tw_context = TwContextGetter(request).get_tw_context()
        form = ExportScreenNameForm(request.POST)
        if form.is_valid():
            screen_name_to_export = form.cleaned_data['tw_user_to_export']
            ok, task_par_screen_name, err_msg_for_user = resolve_screen_name_for_export(tw_context,
                                                                                        screen_name_to_export)
            if ok:
                redirect_url = create_task_for_user(request,
                                                    Task.TaskType.EXPORT.name,
                                                    "export_ok",
                                                    par_exp_screen_name=task_par_screen_name)
            else:
                redirect_url = redirect_to_error_view(request, err_msg_for_user)
            return HttpResponseRedirect(redirect_url)

        else:
            return render(request, 'tfei/export.html', {'form': form})


class ExportOkView(TemplateView):
    template_name = "tfei/export-ok.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        return {}


class ImportView(View):
    template_name = "tfei/import.html"

    @requires_auth
    def get(self, request, *args, **kwargs):
        u = TwContextGetter(request).get_tw_context()
        user_id = u['user_id']
        task_exists, msg_context = task_for_user_exists(user_id)
        if task_exists:
            return render(request, 'tfei/import.html', {'msg_context': msg_context})
        else:
            form = ImportFileForm()
            return render(request, "tfei/import.html", {'form': form})

    @requires_auth
    def post(self, request, *args, **kwargs):
        file_to_import = request.FILES.get('file_to_import')
        if not file_to_import:
            return HttpResponseRedirect(redirect_to_error_view(request, "file to upload is missing"))

        tw_context = TwContextGetter(request).get_tw_context()
        form = ImportFileForm(request.POST, request.FILES)
        if form.is_valid():
            ok, path_file, err_msg_for_user = handle_upload_file(file_to_import, tw_context)
            if ok:
                redirect_url = create_task_for_user(request,
                                                    Task.TaskType.IMPORT.name,
                                                    "import_ok",
                                                    par_imp_file_name=path_file)
            else:
                redirect_url = redirect_to_error_view(request, err_msg_for_user)
            return HttpResponseRedirect(redirect_url)

        else:
            return render(request, "tfei/import.html", {'form': form})


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
        task = retrieve_task_for_user(task_id, user_id)

        path_file = Path(task.finished_output)
        if exists(path_file) and isfile(path_file) \
                and validate_user_file_path(user_screen_name, str(path_file.absolute())):
            with open(path_file, 'r') as f:
                resp = HttpResponse(f.read(), content_type="text/csv")
                resp['Content-Disposition'] = f"attachment;filename={os.path.basename(path_file)}"
                return resp
        else:
            raise ObjectDoesNotExist()


class TaskDetailsView(TemplateView):
    template_name = "tfei/task-details.html"

    @requires_tw_context
    def get_context_data(self, **kwargs):
        tw_context = TwContextGetter(self.request).get_tw_context()
        user_id = tw_context['user_id']
        task_id = kwargs['task_id']
        task = retrieve_task_for_user(task_id, user_id)
        context_data = {'task_context': task}
        if task.task_type == Task.TaskType.IMPORT.name:
            add_deserialized_output_and_details(task, context_data)
        return context_data


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
