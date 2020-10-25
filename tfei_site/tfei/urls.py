from django.urls import path, re_path
from django.views.generic.base import RedirectView

from . import views
from .views import TwAuthenticateRedirectView

favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
        re_path(r'^favicon\.ico$', favicon_view),
        path('', views.index, name='index'),
        path('main', views.main_v, name='main'),
        path('tw_auth', TwAuthenticateRedirectView.as_view(), name='tw_auth'),
        path('tw_auth_callback', views.tw_auth_callback, name='tw_auth_callback'),
        path('export', views.export_v, name='export'),
        path('import', views.import_v, name='import'),
        path('logout', views.logout_v, name='logout')

        ]
