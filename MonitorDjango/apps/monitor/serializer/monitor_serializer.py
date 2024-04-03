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

    def __init__(self, *args, **kwargs):
        # 从kwargs中移除fields，如果不存在则默认为None
        fields = kwargs.pop('fields', None)

        # 调用父类构造函数
        super(MonitorSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            # 如果指定了fields，则删除所有未在fields中声明的字段
            allowed = set(fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def get_visits(self, obj):
        # 检查是否需要展示嵌套数据
        if self.context.get('need_nested', False):
            # 假设VisitSerializer已定义且正确实现
            return VisitSerializer(obj.visits.all(), many=True).data
        else:
            # 如果不需要嵌套数据，返回None或其他适当的值
            return None

    class Meta:
        model = WebsiteModel
        fields = ['id', 'domain', 'site_name', 'deploy_status', 'data_transfer_total', 'visit_total',
                  'visitor_total','ip_total',
                  'error_total', 'malicious_request_total', 'request_per_second',
                  'visits'
                  ]
