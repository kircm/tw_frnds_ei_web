from django.urls import path, re_path
from django.views.generic.base import RedirectView

from .views import ExportView
from .views import ImportView
from .views import IndexView
from .views import LogoutView
from .views import MainView
from .views import TwAuthCallbackView
from .views import TwAuthenticateRedirectView

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    re_path(r'^favicon\.ico$', favicon_view),
    path('', IndexView.as_view(), name='index'),
    path('main', MainView.as_view(), name='main'),
    path('export', ExportView.as_view(), name='export'),
    path('import', ImportView.as_view(), name='import'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('tw_auth', TwAuthenticateRedirectView.as_view(), name='tw_auth'),
    path('tw_auth_callback', TwAuthCallbackView.as_view(), name='tw_auth_callback'),
]
