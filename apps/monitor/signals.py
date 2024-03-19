import logging
from datetime import datetime

from django.db import transaction, models
from django.db.models import F, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from monitor.models import VisitModel, TodayTotalModel, WebsiteModel

logger = logging.getLogger('monitor')


@receiver(post_save, sender=VisitModel)
def update_total(sender, instance, created, **kwargs):
    if created:
        traffic_date = timezone.now().date()
        website = instance.site

        # 使用get_or_create更新或创建TodayTotalModel实例
        today_total, _ = TodayTotalModel.objects.get_or_create(
            website=website,
            traffic_time=traffic_date,
            defaults={'ip_today': 0, 'visit_today': 0, 'visitor_today': 0, 'traffic_today': 0}
        )

        # 简化统计逻辑
        ip_count = VisitModel.objects.filter(site=website, visit_time__date=traffic_date).values(
            'remote_addr').distinct().count()
        visitor_count = VisitModel.objects.filter(site=website, visit_time__date=traffic_date).values('remote_addr',
                                                                                                      'user_agent').distinct().count()
        visitor_total = VisitModel.objects.filter(site=website).values('remote_addr', 'user_agent').distinct().count()
        visit_total = VisitModel.objects.filter(site=website).count()
        data_transfer_total = \
            VisitModel.objects.filter(site=website).aggregate(total_data_transfer=Sum('data_transfer'))[
                'total_data_transfer'] or 0

        # 更新TodayTotalModel实例
        TodayTotalModel.objects.filter(pk=today_total.pk).update(
            visit_today=F('visit_today') + 1,
            visitor_today=visitor_count,
            traffic_today=F('traffic_today') + instance.data_transfer,
            ip_today=ip_count
        )

        # 更新WebsiteModel实例，尽量避免在循环中操作
        WebsiteModel.objects.filter(pk=website.pk).update(
            ip_total=visitor_total,
            visit_total=visit_total,
            data_transfer_total=data_transfer_total,
            visitor_total=visitor_count
        )
