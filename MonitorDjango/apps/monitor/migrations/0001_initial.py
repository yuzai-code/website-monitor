# Generated by Django 3.2.25 on 2024-03-09 09:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='WebsiteModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('site_name', models.CharField(blank=True, max_length=100, null=True, verbose_name='站点名称')),
                ('site_type', models.CharField(blank=True, max_length=100, null=True, verbose_name='站点类型')),
                ('domain', models.CharField(blank=True, max_length=100, null=True, verbose_name='域名')),
                ('url', models.CharField(blank=True, max_length=100, null=True, verbose_name='访问完整URL')),
                ('deploy_status', models.IntegerField(choices=[(0, '未部署'), (1, '已部署')], default=0, verbose_name='部署状态')),
            ],
            options={
                'verbose_name': '站点信息',
                'verbose_name_plural': '站点信息',
                'db_table': 't_website',
            },
        ),
        migrations.CreateModel(
            name='VisitModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('visit_time', models.DateTimeField(auto_now_add=True, verbose_name='访问时间')),
                ('ip', models.GenericIPAddressField(verbose_name='访问IP')),
                ('user_agent', models.CharField(max_length=100, verbose_name='User-Agent')),
                ('path', models.CharField(max_length=100, verbose_name='访问路径')),
                ('method', models.CharField(max_length=100, verbose_name='请求方法')),
                ('status_code', models.IntegerField(verbose_name='HTTP状态码')),
                ('data_transfer', models.BigIntegerField(verbose_name='数据传输总量')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitor.websitemodel', verbose_name='站点')),
            ],
            options={
                'verbose_name': '访问信息',
                'verbose_name_plural': '访问信息',
                'db_table': 't_visit',
            },
        ),
        migrations.CreateModel(
            name='TrafficModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('traffic_time', models.DateField(unique=True, verbose_name='流量日期')),
                ('traffic', models.BigIntegerField(verbose_name='当天传输数据量')),
                ('page_view', models.IntegerField(verbose_name='当天页面访问量')),
                ('unique_visitor', models.IntegerField(verbose_name='当天独立访客量')),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitor.websitemodel', verbose_name='站点')),
            ],
            options={
                'verbose_name': '流量信息',
                'verbose_name_plural': '流量信息',
                'db_table': 't_traffic',
            },
        ),
        migrations.CreateModel(
            name='ResourceModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('ip_total', models.IntegerField(verbose_name='访问IP总数')),
                ('visit_total', models.IntegerField(verbose_name='总访问量')),
                ('data_transfer_total', models.BigIntegerField(verbose_name='总数据传输量')),
                ('visitor_total', models.IntegerField(verbose_name='总访客数')),
                ('date', models.DateField(auto_now_add=True, verbose_name='日期')),
                ('website', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitor.websitemodel', verbose_name='站点')),
            ],
            options={
                'verbose_name': '资源信息',
                'verbose_name_plural': '资源信息',
                'db_table': 't_resource',
            },
        ),
    ]
