from django.contrib import admin
from django.contrib.auth.models import Permission

from .models import Task
from .models import TwUser

admin.site.register(Task)
admin.site.register(TwUser)
admin.site.register(Permission)
