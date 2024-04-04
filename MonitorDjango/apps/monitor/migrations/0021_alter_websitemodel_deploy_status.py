# Generated by Django 3.2.25 on 2024-03-20 05:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0020_websitemodel_malicious_request_total'),
    ]

    operations = [
        migrations.AlterField(
            model_name='websitemodel',
            name='deploy_status',
            field=models.IntegerField(choices=[(0, '未部署'), (1, '已部署')], default=1, verbose_name='部署状态'),
        ),
    ]