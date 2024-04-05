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
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_min(self):
        # 获取过去5分钟内ip数量最多的前10个
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        s = s.filter('range', **{'visit_time': {
            'gte': 'now-5m/m', 'lte': 'now/m'
        }})
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_hour(self):
        # 获取过去一个小时内ip数量最多的前10个
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        s = s.filter('range', **{'visit_time': {'gte': 'now-1h', 'lte': 'now'}})
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_day(self):
        # 获取今天一天内ip数量最多的前10各
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        # 将时间范围过滤调整为过去24小时  # todo 之后可以使用@timestamp
        s = s.filter('range', **{'visit_time': {'gte': 'now-24h/h', 'lte': 'now/h'}})
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def search_ip(self, ip, size=None):
        # 根据ip查询
        s = Search(using=self.es, index=self.index)
        s = s.query(Q('term', domain__keyword=self.domain) & Q('term', remote_addr=ip))
        response = s.execute()
        return response

    # 爬虫检测
    def get_spider_aggregation(self):
        # 创建一个查询实例
        s = Search(using=self.es, index=self.index).filter('term', domain__keyword=self.domain)

        # 使用正则表达式匹配用户代理，以覆盖更广泛的爬虫
        spider_patterns = ['.*Googlebot.*', '.*Baiduspider.*', '.*bingbot.*', '.*YandexBot.*']
        q = Q('bool', should=[Q('regexp', user_agent__keyword=pattern) for pattern in spider_patterns],
              minimum_should_match=1)
        s = s.query(q)

        # 添加其他聚合维度，例如按小时聚合访问
        s.aggs.bucket('spider', 'terms', field='user_agent.keyword').bucket('hourly', 'date_histogram',
                                                                            field='@timestamp',
                                                                            calendar_interval='hour')

        # 尝试执行查询，并捕获潜在的异常
        try:
            response = s.execute()
            return response.aggregations.spider.buckets
        except Exception as e:
            print(f"查询失败: {e}")
            return []
