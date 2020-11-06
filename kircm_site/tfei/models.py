from django.db import models


class Task(models.Model):
    tw_user = models.ForeignKey('TwUser', on_delete=models.PROTECT)
    tw_screen_name_for_task = models.CharField(max_length=30)

    task_type = models.CharField(max_length=20)
    task_status = models.CharField(max_length=20)
    task_par_tw_id = models.BigIntegerField()
    task_par_f_name = models.CharField(max_length=100)

    pending_at = models.DateTimeField(auto_now_add=True)
    running_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    finished_ok = models.BooleanField(null=True)
    finished_details = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TwUser(models.Model):
    tw_id = models.BigIntegerField(primary_key=True)
    tw_screen_name = models.CharField(max_length=30)

    tw_token = models.CharField(max_length=100)
    tw_token_sec = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
