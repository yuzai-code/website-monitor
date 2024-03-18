import logging
from datetime import datetime

from django.db import transaction
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from monitor.models import VisitModel, TodayTotalModel, WebsiteModel

logger = logging.getLogger('monitor')


@receiver(post_save, sender=VisitModel)
def update_total(sender, instance, created, **kwargs):
    traffic_date = timezone.now().date()
    if created:
        with transaction.atomic():
            # 首先尝试获取今日的记录
            today_total, created = TodayTotalModel.objects.get_or_create(
                website=instance.site,
                traffic_time=traffic_date,
                defaults={
                    'visit_today': 0,
                    'visitor_today': 0,
                    'traffic_today': 0,
                    'ip_today': 0
                }
            )
            # 统计该站点下当天所有不同的ip数
            ip_count = VisitModel.objects.filter(site=instance.site, visit_time__date=traffic_date).values(
                'remote_addr').distinct().count()

            # 统计该站点下当天所有不同的访客数
            visitor_count = VisitModel.objects.filter(site=instance.site, visit_time__date=traffic_date).values(
                'remote_addr', 'user_agent').distinct().count()

            # 使用F表达式更新字段值
            today_total = TodayTotalModel.objects.filter(
                pk=today_total.pk
            )
            today_total.update(
                visit_today=F('visit_today') + 1,
                visitor_today=visitor_count,
                traffic_today=F('traffic_today') + instance.data_transfer,
                ip_today=ip_count
            )

            # 重新获取更新后的实例以打印日志
            logger.info(
                f'更新今日总数: {today_total, visitor_count, ip_count} ')

            # WebsiteModel中的总数
            # website = WebsiteModel.objects.filter(id=instance.site.id).update(
            #     visit_total=F('visit_total') + 1,
            #     visitor_total=F('visitor_total') + visitor_count,
            #     data_transfer_total=F('data_transfer_total') + instance.data_transfer,
            #     ip_total=F('ip_total') + ip_count
            # )
            # logger.info(f'更新总数: {website}')
            # print(f'更新总数: {total}')
    else:
        # 如果是更新的访问记录，更新总流量
        print('2222')
