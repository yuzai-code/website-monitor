# Generated by Django 3.2.25 on 2024-04-05 19:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('monitor', '0025_auto_20240405_1718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='websitemodel',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='用户1'),
        ),
    ]
