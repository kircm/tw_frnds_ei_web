# Generated by Django 3.1.2 on 2020-11-09 13:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tfei', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='task_par_f_name',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_par_tw_id',
            field=models.BigIntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_status',
            field=models.CharField(choices=[('CREATED', 'Created'), ('PENDING', 'Pending'), ('RUNNING', 'Running'), ('FINISHED', 'Finished'), ('CANCELED', 'Canceled')], max_length=20),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_type',
            field=models.CharField(choices=[('IMPORT', 'Import'), ('EXPORT', 'Export')], max_length=20),
        ),
        migrations.AlterField(
            model_name='twuser',
            name='tw_token',
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='twuser',
            name='tw_token_sec',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
