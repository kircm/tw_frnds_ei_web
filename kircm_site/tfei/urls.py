from django.urls import path

from .views import ErrorView
from .views import ExportView
from .views import ImportView
from .views import IndexView
from .views import LogoutView
from .views import MainMenuView
from .views import MainView
from .views import TwAuthCallbackView
from .views import TwAuthenticateRedirectView

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('main', MainView.as_view(), name='main'),
    path('export', ExportView.as_view(), name='export'),
    path('import', ImportView.as_view(), name='import'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('tw_auth', TwAuthenticateRedirectView.as_view(), name='tw_auth'),
    path('tw_auth_callback', TwAuthCallbackView.as_view(), name='tw_auth_callback'),
    path('mainmenu', MainMenuView.as_view(), name='main_menu'),
    path('error', ErrorView.as_view(), name='error_view'),
]
