# Generated by Django 3.2.25 on 2024-03-18 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0015_auto_20240318_0656'),
    ]

    operations = [
        migrations.AddField(
            model_name='websitemodel',
            name='error_total',
            field=models.IntegerField(default=0, verbose_name='错误数'),
        ),
        migrations.AddField(
            model_name='websitemodel',
            name='request_per_second',
            field=models.FloatField(blank=True, null=True, verbose_name='每秒请求数'),
        ),
    ]
