from django.urls import path
from django.views.generic import TemplateView

from .views import ErrorView
from .views import ExportOkView
from .views import ExportView
from .views import ImportOkView
from .views import ImportView
from .views import LogoutView
from .views import MainMenuView
from .views import TwAuthCallbackView
from .views import TwAuthenticateRedirectView

urlpatterns = [
    path('', TemplateView.as_view(template_name="tfei/index.html"), name='index'),
    path('tw_auth', TwAuthenticateRedirectView.as_view(), name='tw_auth'),
    path('tw_auth_callback', TwAuthCallbackView.as_view(), name='tw_auth_callback'),
    path('auth_error', TemplateView.as_view(template_name="tfei/auth-nk.html"), name='auth_error'),
    path('mainmenu', MainMenuView.as_view(), name='main_menu'),
    path('export', ExportView.as_view(), name='export'),
    path('export_ok', ExportOkView.as_view(), name='export_ok'),
    path('import', ImportView.as_view(), name='import'),
    path('import_ok', ImportOkView.as_view(), name='import_ok'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('error', ErrorView.as_view(), name='error_view'),
]
