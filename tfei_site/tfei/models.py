from django.db import models


class Task(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    tw_screen_name = models.CharField(max_length=30)
    tw_id = models.BigIntegerField()

    task_type = models.CharField(max_length=6)
    task_status = models.CharField(max_length=20)

    pending_at = models.DateTimeField(auto_now_add=True)
    running_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    finished_ok = models.BooleanField(null=True)
    finished_details = models.TextField(blank=True)


