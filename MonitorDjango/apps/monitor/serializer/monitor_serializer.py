from rest_framework import serializers

from monitor.models import WebsiteModel, VisitModel


# 序列化器
class MonitorSerializer(serializers.ModelSerializer):
    total_visits = serializers.IntegerField(source='visit_total', read_only=True)
    class Meta:
        model = WebsiteModel
        fields = ['id', 'domain', 'site_name', 'deploy_status', 'ip_total', 'visit_total', 'data_transfer_total',
                  'visitor_total', 'error_total', 'malicious_request_total', 'request_per_second',
                  'total_visits'

                  ]


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitModel
        fields = ['id', 'site', 'visit_time','remote_addr', 'user_agent',
                  'path', 'method', 'status_code', 'data_transfer', 'http_referer', 'malicious_request',
                  'http_x_forwarded_for', 'request_time']