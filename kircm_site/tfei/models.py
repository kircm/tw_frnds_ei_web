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
        CANCELED = 'CANCELED'

    class UserTaskExisting(Exception):
        pass

    tw_user = models.ForeignKey('TwUser', on_delete=models.PROTECT)
    tw_screen_name_for_task = models.CharField(max_length=30)

    task_type = models.CharField(max_length=20, choices=TaskType.choices)
    task_status = models.CharField(max_length=20, choices=TaskStatus.choices)
    task_par_tw_id = models.BigIntegerField(null=True)
    task_par_f_name = models.CharField(max_length=100, null=True)

    pending_at = models.DateTimeField(auto_now_add=True)
    running_at = models.DateTimeField(blank=True, null=True)
    finished_at = models.DateTimeField(blank=True, null=True)

    finished_ok = models.BooleanField(null=True)
    finished_details = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.task_type} - {self.tw_user} - {self.task_status} - updated-at: {self.updated_at}"

    @classmethod
    def create_from_tw_context(cls, task_type, tw):
        u_id = tw['user_id']
        u = TwUser.objects.get(tw_id=u_id)
        existing = cls.objects.filter(
            tw_user=u,
            task_status=cls.TaskStatus.PENDING
        )
        if existing:
            raise cls.UserTaskExisting()
        t = cls.objects.create(
            tw_user=u,
            tw_screen_name_for_task=u.tw_screen_name,
            task_type=cls.TaskType.EXPORT,
            task_status=cls.TaskStatus.PENDING
        )
        t.save()


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
        u, created = cls.objects.get_or_create(tw_id=tw['user_id'])
        u.tw_screen_name = tw['user_screen_name']
        u.tw_token = tw['oauth_final_token']
        u.tw_token_sec = tw['oauth_final_token_secret']
        u.save()

    @classmethod
    def clear_tw_tokens(cls, tw_id):
        u = cls.objects.get(tw_id=tw_id)
        u.tw_token = None
        u.tw_token_sec = None
        u.save()
