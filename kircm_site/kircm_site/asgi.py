"""
ASGI config for kircm_site project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

# ----------------------------------------------------
# MK: Notes about trying ASGI on pythonanywhere.com
# 2020 12 19
# ----------------------------------------------------
#
# ASGI not supported in pythonanywhere.com
#
# We tried the django channels fall-back alternative with no success:
# https://channels.readthedocs.io/en/stable/installation.html
#
# Error when loading any view for the first time:
#
#   /var/log/kircm.pythonanywhere.com.error.log
#
#     2020-12-19 12:31:25,096: Error running WSGI application
#     2020-12-19 12:31:25,097: TypeError: __call__() missing 1 required positional argument: 'send'
#

import os

from channels.routing import ProtocolTypeRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kircm_site.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # Just HTTP for now. (We can add other protocols later.)
})
