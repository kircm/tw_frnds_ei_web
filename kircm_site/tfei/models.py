from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class Task(models.Model):
    class TaskType(models.TextChoices):
        IMPORT = 'IMPORT'
        EXPORT = 'EXPORT'

    class TaskStatus(models.TextChoices):
        CREATED = 'CREATED'
        PENDING = 'PENDING'
        RUNNING = 'RUNNING'
        FINISHED = 'FINISHED'

    class UserTaskExisting(Exception):
        pass

    tw_user = models.ForeignKey('TwUser', on_delete=models.PROTECT)
    tw_screen_name_for_task = models.CharField(max_length=30)

    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    task_status = models.CharField(max_length=20, choices=TaskStatus.choices)
    par_exp_screen_name = models.CharField(max_length=30, blank=True, null=True)
    par_imp_file_name = models.CharField(max_length=100, blank=True, null=True)

    pending_at = models.DateTimeField(blank=True, null=True)
    running_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    finished_ok = models.BooleanField(blank=True, null=True)
    finished_output = models.TextField(blank=True, null=True)
    finished_details = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.tw_user} - {self.task_type} - {self.task_status} - updated-at: {self.updated_at}"

    @classmethod
    def get_existing_not_finished_for_user(cls, u):
        return cls.objects.filter(tw_user=u).exclude(task_status__exact=cls.TaskStatus.FINISHED)

    @classmethod
    def create_from_tw_context(cls, task_type, tw, par_exp_screen_name=None, par_imp_file_name=None):
        u = TwUser.objects.get(pk=tw['user_id'])

        existing_not_finished = cls.get_existing_not_finished_for_user(u)
        if existing_not_finished:
            # Stop creating new task for user - there is one pending or running
            raise cls.UserTaskExisting()

        cls.objects.create(
            tw_user=u,
            tw_screen_name_for_task=u.tw_screen_name,
            task_type=task_type,
            par_exp_screen_name=par_exp_screen_name,
            par_imp_file_name=par_imp_file_name,
            task_status=cls.TaskStatus.CREATED
        )

    @classmethod
    def retrieve_user_tasks_with_tw_context(cls, tw_context):
        u = TwUser.objects.get(pk=tw_context['user_id'])
        tasks_for_user = cls.objects.filter(tw_user=u).order_by('-created_at')
        fields = ('id',
                  'tw_screen_name_for_task',
                  'task_type',
                  'task_status',
                  'par_exp_screen_name',
                  'finished_ok',
                  'finished_output',
                  'finished_details',
                  'created_at',
                  'finished_at',
                  'finished_output',
                  'finished_details')
        task_list = list(tasks_for_user.values(*fields))
        return task_list


class TwUser(models.Model):
    tw_id = models.BigIntegerField(primary_key=True)
    tw_screen_name = models.CharField(max_length=30)

    tw_token = models.CharField(max_length=100, null=True)
    tw_token_sec = models.CharField(max_length=100, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tw_screen_name}({self.tw_id})"

    @classmethod
    def create_or_update_from_tw_context(cls, tw):
        u, created = cls.objects.get_or_create(pk=tw['user_id'])
        u.tw_screen_name = tw['user_screen_name']
        u.tw_token = tw['oauth_final_token']
        u.tw_token_sec = tw['oauth_final_token_secret']
        u.save()

    @classmethod
    def clear_tw_tokens(cls, tw_id):
        try:
            u = cls.objects.get(pk=tw_id)
            u.tw_token = None
            u.tw_token_sec = None
            u.save()
        except ObjectDoesNotExist:
            # user got deleted from admin site?
            # in any case user is definitely logged-out!
            pass
