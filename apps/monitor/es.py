from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search


# 聚合
class Aggregation:
    def __init__(self, index):
        self.index = index
        self.es = Elasticsearch()

    def get_ip_aggregation(self):
        # 聚合ip查询
        s = Search(using=self.es, index=self.index)
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=10)
        response = s.execute()
        return response.aggregations.ip.buckets
