from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


# es = Elasticsearch()


# 聚合
class Aggregation:
    def __init__(self, index, domain=None):
        self.index = index
        self.es = Elasticsearch()
        self.domain = domain

    def get_ip_aggregation(self, size=None):
        # 聚合ip查询
        s = Search(using=self.es, index=self.index)
        print(self.domain)
        s = s.filter('term', domain__keyword=self.domain)
        s.aggs.bucket('ip', 'terms', field='http_x_forwarded_for', size=size)
        response = s.execute()
        return response.aggregations.ip.buckets

    def search_ip(self, ip, size=None):
        # 根据ip查询
        s = Search(using=self.es, index=self.index)
        s = s.query(Q('term', domain__keyword=self.domain) & Q('term', http_x_forwarded_for=ip))
        response = s.execute()
        return response
