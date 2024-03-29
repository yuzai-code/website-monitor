import logging
from datetime import datetime

from django.db import transaction, models
from django.db.models import F, Sum, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from monitor.models import VisitModel, TodayTotalModel, WebsiteModel

logger = logging.getLogger('monitor')

IP_LIST = {
    'remote_addr': 'remote_addr',
    'http_x_forwarded_for': 'http_x_forwarded_for'
}


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

        # 统计每天的访问量、访客量、IP数、流量总量
        ip_count = VisitModel.objects.filter(site=website, visit_time__date=traffic_date).values(
            IP_LIST['http_x_forwarded_for']).distinct().count()
        visit_count = VisitModel.objects.filter(site=website, visit_time__date=traffic_date).count()
        visitor_count = VisitModel.objects.filter(site=website, visit_time__date=traffic_date).values(
            IP_LIST['http_x_forwarded_for'],
            'user_agent').distinct().count()

        # 统计站点的总访问量、访客量、IP数、流量总量
        ip_total = VisitModel.objects.filter(site=website).values(IP_LIST['http_x_forwarded_for']).distinct().count()
        visitor_total = VisitModel.objects.filter(site=website).values(IP_LIST['http_x_forwarded_for'],
                                                                       'user_agent').distinct().count()
        visit_total = VisitModel.objects.filter(site=website).count()
        data_transfer_total = \
            VisitModel.objects.filter(site=website).aggregate(total_data_transfer=Sum('data_transfer'))[
                'total_data_transfer'] or 0
        error_total = VisitModel.objects.filter(
            Q(site=website) & Q(status_code__gte=400) & Q(status_code__lte=599)).count()
        request_per_second = VisitModel.objects.filter(site=website).count() / (
                timezone.now() - website.create_time).total_seconds()

        # 更新TodayTotalModel实例
        TodayTotalModel.objects.filter(pk=today_total.pk).update(
            visit_today=visit_count,
            visitor_today=visitor_count,
            traffic_today=F('traffic_today') + instance.data_transfer,
            ip_today=ip_count
        )

        # 更新WebsiteModel实例，尽量避免在循环中操作
        WebsiteModel.objects.filter(pk=website.pk).update(
            ip_total=ip_total,
            visit_total=visit_total,
            data_transfer_total=data_transfer_total,
            visitor_total=visitor_total,
            error_total=error_total
        )
        logger.info(f'站点{website.domain}统计成功！')
