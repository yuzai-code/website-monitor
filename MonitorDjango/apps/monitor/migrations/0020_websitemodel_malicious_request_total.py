# Generated by Django 3.2.25 on 2024-03-19 08:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0019_alter_logfilemodel_website'),
    ]

    operations = [
        migrations.AddField(
            model_name='websitemodel',
            name='malicious_request_total',
            field=models.IntegerField(default=0, verbose_name='恶意请求数'),
        ),
    ]
