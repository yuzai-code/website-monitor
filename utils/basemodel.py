# -*- coding: utf-8 -*-
from django.db import models


class BaseModel(models.Model):
    """
    基础模型
    """
    create_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    status = models.BooleanField(default=True, verbose_name='状态')

    class Meta:
        abstract = True
        verbose_name = '基础模型'
        verbose_name_plural = verbose_name
        ordering = ['-id']
        get_latest_by = 'create_time'
        db_table = 't_base_model'
        app_label = 'base'
        default_permissions = ()
        permissions = (
            ('view_basemodel', 'Can view 基础模型'),
        )

    def __str__(self):
        return self.create_time.strftime('%Y-%m-%d %H:%M:%S')

    def __unicode__(self):
        return self.create_time.strftime('%Y-%m-%d %H:%M:%S')
