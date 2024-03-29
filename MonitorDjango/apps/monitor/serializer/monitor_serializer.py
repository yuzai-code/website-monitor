from rest_framework import serializers

from monitor.models import WebsiteModel


# 序列化器
class MonitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebsiteModel
        fields = ['id', 'domain', 'site_name', 'deploy_status', 'ip_total', 'visit_total', 'data_transfer_total',
                  'visitor_total', 'request_per_second']
