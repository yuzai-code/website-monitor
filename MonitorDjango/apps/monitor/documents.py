from django_elasticsearch_dsl import Document, fields
from django_elasticsearch_dsl.registries import registry

from monitor.models import VisitModel, WebsiteModel


@registry.register_document
class WebsiteDocument(Document):
    user_id = fields.IntegerField(attr='user.id')

    class Index:
        name = 'website'
        settings = {
            "number_of_shards": 1,
        }

    class Django:
        model = WebsiteModel
        fields = [
            'site_name',
            'site_type',
            'domain',
            'deploy_status',
            'ip_total',
            'visit_total',
            'data_transfer_total',
            'visitor_total',
            'error_total',
            'malicious_request_total',
            'request_per_second'
        ]


@registry.register_document
class VisitDocument(Document):
    domain = fields.TextField(
        attr='site.domain',
        fields={
            'keyword': fields.KeywordField(),
        }
    )
    remote_addr = fields.KeywordField()
    http_x_forwarded_for = fields.KeywordField()
    user_id = fields.IntegerField(attr='user.id')

    class Index:
        name = 'visit'
        settings = {
            "number_of_shards": 1,
        }

    class Django:
        model = VisitModel
        fields = [
            'visit_time',
            'user_agent',
            'path',
            'method',
            'status_code',
            'data_transfer',
            'http_referer',
            'malicious_request',
            'request_time'
        ]
