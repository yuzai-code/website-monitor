import logging
from datetime import datetime

from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from monitor.models import VisitModel, TodayTotalModel, WebsiteModel

logger = logging.getLogger('monitor')


@receiver(post_save, sender=VisitModel)
def update_total(sender, instance, created, **kwargs):
    logger.info(f'更新总数: {instance}')
    """
    更新总数
    """
    if created:
        # 更新TodayTotalModel中的数据
        today_total, created = TodayTotalModel.objects.get_or_create(
            website=instance.site,
            traffic_time=timezone.now().date(),
            defaults={'ip_today': 0, 'traffic_today': 0, 'visit_today': 0, 'visitor_today': 0}
        )
        today_total.ip_today = F('ip_today') + 1
        today_total.traffic_today = F('traffic_today') + instance.data_transfer
        today_total.visit_today = F('visit_today') + 1
        today_total.visitor_today = F('visitor_today') + 1
        today_total.save()
        # 更新TotalModel中的数据
        total, created = WebsiteModel.objects.get_or_create(
            website=instance.site,
            defaults={'ip_total': 0, 'visit_total': 0, 'data_transfer_total': 0, 'visitor_total': 0}
        )
        total.ip_total = F('ip_total') + 1
        total.visit_total = F('visit_total') + 1
        total.data_transfer_total = F('data_transfer_total') + instance.data_transfer
        total.visitor_total = F('visitor_total') + 1
        total.save()
    else:
        # 如果是更新的访问记录，更新总流量
        pass
