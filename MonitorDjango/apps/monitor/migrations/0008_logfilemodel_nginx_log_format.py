# Generated by Django 3.2.25 on 2024-03-13 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0007_logfilemodel'),
    ]

    operations = [
        migrations.AddField(
            model_name='logfilemodel',
            name='nginx_log_format',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Nginx日志格式'),
        ),
    ]
