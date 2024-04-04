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
        s.aggs.bucket('ip', 'terms', field='http_x_forwarded_for', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_min(self):
        # 获取过去5分钟内ip数量最多的前10个
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        s = s.filter('range', **{'visit_time': {
            'gte': 'now-5m/m', 'lte': 'now/m'
        }})
        s.aggs.bucket('ip', 'terms', field='http_x_forwarded_for', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_hour(self):
        # 获取过去一个小时内ip数量最多的前10个
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        s = s.filter('range', **{'visit_time': {'gte': 'now-1h', 'lte': 'now'}})
        s.aggs.bucket('ip', 'terms', field='http_x_forwarded_for', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_day(self):
        # 获取今天一天内ip数量最多的前10各
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        # 将时间范围过滤调整为过去24小时  # todo 之后可以使用@timestamp
        s = s.filter('range', **{'visit_time': {'gte': 'now-24h/h', 'lte': 'now/h'}})
        s.aggs.bucket('ip', 'terms', field='http_x_forwarded_for', size=15)
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
