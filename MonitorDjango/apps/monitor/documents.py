from elasticsearch_dsl import Document, Text, Keyword, Integer, Date, Float
from datetime import datetime

# 定义 normalizer



class VisitDocument(Document):
    domain = Text(fields={
        'keyword': Keyword()
    })
    remote_addr = Keyword()
    http_x_forwarded_for = Keyword()
    user_id = Integer()
    path = Keyword()
    visit_time = Date()
    user_agent = Keyword(normalizer='my_normalizer')
    method = Keyword()
    HTTP_protocol = Keyword()
    status_code = Keyword()
    data_transfer = Integer()
    http_referer = Keyword()
    malicious_request = Keyword()
    request_time = Float()

    class Index:
        # name = 'visit'
        name = 'visit_new'
        settings = {
            "number_of_shards": 2,
        }

    def save(self, **kwargs):
        # 指定索引名称以保存文档
        self.meta.index = self.Index.name
        return super().save(**kwargs)
