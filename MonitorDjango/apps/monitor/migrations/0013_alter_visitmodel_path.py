# Generated by Django 3.2.25 on 2024-03-16 11:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0012_alter_todaytotalmodel_traffic_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitmodel',
            name='path',
            field=models.CharField(blank=True, max_length=1000, null=True, verbose_name='访问路径'),
        ),
    ]