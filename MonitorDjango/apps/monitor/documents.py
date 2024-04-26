from elasticsearch_dsl import Document, Text, Keyword, Integer, Date, Float, connections, Index


# 定义 Elasticsearch 文档
class VisitDocument(Document):
    domain = Text(fields={'keyword': Keyword()})
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
        name = 'visit_new'
        settings = {
            'number_of_shards': 2,
            'analysis': {
                'normalizer': {
                    'my_normalizer': {
                        'type': 'custom',
                        'filter': ['lowercase', 'asciifolding']
                    }
                }
            }
        }


# # 连接到 Elasticsearch
# connections.create_connection(hosts=['localhost'])
#
# # 删除旧的索引（如果存在）
# if VisitDocument._index.exists():
#     VisitDocument._index.delete()
#
# # 创建新索引
# VisitDocument.init()
# print("索引创建成功")
