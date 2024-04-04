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

    def get_10_ip_aggregation(self):
        # 获取ip前10
        s = Search(using=self.es, index=self.index)
        s = s.filter('range', **{'@timestamp': {'gte': 'now-24h', 'lte': 'now'}})
        s.aggs.bucket('ip', 'terms', field='http_x_forwarded_for', size=10)
        response = s.execute()
        return response.aggregations.ip.buckets

    def search_ip(self, ip, size=None):
        # 根据ip查询
        s = Search(using=self.es, index=self.index)
        s = s.query(Q('term', domain__keyword=self.domain) & Q('term', http_x_forwarded_for=ip))
        response = s.execute()
        return response

    # 爬虫检测
    def get_spider_aggregation(self):
        # 添加聚合查询来识别常见的爬虫
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        # 匹配常见的爬虫
        s = s.filter('terms',
                     user_agent__keyword=['Googlebot', 'Baiduspider', 'bingbot', 'YandexBot', 'Sogou', 'Exabot',
                                          'ia_archiver', 'facebookexternalhit', 'Twitterbot', 'rogerbot', 'linkedinbot',
                                          'embedly', 'quora link preview', 'showyoubot', 'outbrain', 'pinterest',
                                          'developers\.google', 'slackbot', 'vkShare', 'W3C_Validator'])
        s.aggs.bucket('spider', 'terms', field='user_agent.keyword')
        response = s.execute()
        return response.aggregations.spider.buckets