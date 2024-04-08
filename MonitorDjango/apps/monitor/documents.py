from elasticsearch_dsl import Document, Text, Keyword, Integer, Date, Float
from datetime import datetime

class VisitDocument(Document):
    domain = Text()
    remote_addr = Keyword()
    http_x_forwarded_for = Keyword()
    user_id = Integer()
    path = Text()
    visit_time = Date()
    user_agent = Text()
    method = Keyword()
    HTTP_protocol = Keyword()
    status_code = Text()
    data_transfer = Integer()
    http_referer = Text()
    malicious_request = Keyword()
    request_time = Float()

    class Index:
        name = 'visit'
        settings = {
            "number_of_shards": 2,
        }

    def save(self, **kwargs):
        # 指定索引名称以保存文档
        self.meta.index = self.Index.name
        return super().save(**kwargs)