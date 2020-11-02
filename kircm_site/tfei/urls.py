from django.urls import path
from django.views.generic import TemplateView

from .views import ErrorView
from .views import MainMenuView
from .views import TwAuthCallbackView
from .views import TwAuthenticateRedirectView

urlpatterns = [
    path('', TemplateView.as_view(template_name='tfei/index.html'), name='index'),
    path('main', TemplateView.as_view(template_name='tfei/main.html'), name='main'),
    path('export', TemplateView.as_view(template_name='tfei/export.html'), name='export'),
    path('import', TemplateView.as_view(template_name='tfei/import.html'), name='import'),
    path('logout', TemplateView.as_view(template_name='tfei/logout.html'), name='logout'),
    path('tw_auth', TwAuthenticateRedirectView.as_view(), name='tw_auth'),
    path('tw_auth_callback', TwAuthCallbackView.as_view(), name='tw_auth_callback'),
    path('mainmenu', MainMenuView.as_view(), name='main_menu'),
    path('error', ErrorView.as_view(), name='error_view'),
]
