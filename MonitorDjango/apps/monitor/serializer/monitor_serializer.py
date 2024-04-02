from rest_framework import serializers

from monitor.models import WebsiteModel, VisitModel


class VisitSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisitModel
        fields = ['id', 'site', 'visit_time', 'remote_addr', 'user_agent',
                  'path', 'method', 'status_code', 'data_transfer', 'http_referer', 'malicious_request',
                  'http_x_forwarded_for', 'request_time']


# 序列化器
class MonitorSerializer(serializers.ModelSerializer):
    visits = serializers.SerializerMethodField()

    def get_visits(self, obj):
        # 是否需要展示嵌套数据
        if self.context.get('need_nested', False):
            return VisitSerializer(obj.visits.all(), many=True).data
        return None

    class Meta:
        model = WebsiteModel
        fields = ['id', 'domain', 'site_name', 'deploy_status',
                  'error_total', 'malicious_request_total', 'request_per_second',
                  'visits'
                  ]
