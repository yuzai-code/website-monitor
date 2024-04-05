from datetime import datetime, timedelta

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A


class SpiderAggregation:
    """
    爬虫聚合
    """

    def __init__(self, index, domain):
        self.index = index
        self.es = Elasticsearch()
        self.domain = domain

    def get_spider_aggregation(self, remote_addr):
        # 创建一个查询实例，指定使用的Elasticsearch实例和索引
        s = Search(using=self.es, index=self.index)

        response = s.execute()
        return response.aggregations.ip.buckets
        # # 定义针对不同爬虫的正则表达式过滤器
        # spider_filters = {
        #     "google": Q("regexp", user_agent__keyword=".*Googlebot.*"),
        #     "bing": Q("regexp", user_agent__keyword=".*bingbot.*")
        # }
        #
        # # 创建过滤器聚合
        # spiders_agg = A("filters", filters=spider_filters)
        #
        # # 将过滤器聚合添加到搜索查询中
        # s.aggs.bucket("spiders", spiders_agg)
        #
        # # 尝试执行查询，并捕获潜在的异常
        # try:
        #     response = s.execute()
        #     # 处理聚合结果
        #     for spider_name in response.aggregations.spiders.buckets:
        #         doc_count = response.aggregations.spiders.buckets[spider_name].doc_count
        #         print(f"{spider_name}: {doc_count} hits")
        #     return response.aggregations.spiders.buckets
        # except Exception as e:
        #     print(f"Failed to aggregate spiders: {e}")
        #     return {}
        #


# 统计总的IP与访问量
class TotalIPVisit:

    def __init__(self, index):
        self.index = index
        self.es = Elasticsearch()
        self.two_weeks_ago = datetime.now() - timedelta(weeks=2)  # 计算两周前的日期)
        self.two_weeks_ago_str = self.two_weeks_ago.strftime('%Y-%m-%dT%H:%M:%S')  # 转换为适合Elasticsearch的日期格式字符串)
        self.excluded_user_agents = [
            ".*Googlebot.*",  # 爬虫
            ".*bingbot.*",
        ]
        self.included_user_agents = "compatible; Googlebot/2.1; +http://www.google.com/bot.html",


    def total_visit(self):
        """
        统计过去两周内，排除特定用户代理后的每日访问量。
        """

        static_paths = [
            Q("wildcard", path="*/static/*"),
            Q("wildcard", path="*/media/*"),
        ]

        # 创建搜索对象
        s = Search(using=self.es, index=self.index)

        # 构建排除特定用户代理和静态文件路径的查询
        excluded_queries = [Q("regexp", user_agent=ua) for ua in self.excluded_user_agents] + static_paths

        # 添加排除用户代理为空的条件
        excluded_queries.append(~Q("exists", field="user_agent"))

        # 添加时间范围查询，限制为过去两周
        date_range_query = Q('range', visit_time={'gte': self.two_weeks_ago_str})

        # 将查询条件组合起来
        query = Q('bool', must=[date_range_query], must_not=excluded_queries)

        # 添加查询
        s = s.query(query)

        # 定义日期直方图聚合，以visit_time字段进行按天聚合
        s.aggs.bucket(
            'visits_per_day',
            'date_histogram',
            field='visit_time',
            calendar_interval='day'
        )

        # 执行查询
        response = s.execute()

        # 遍历聚合结果并打印每天的访问量
        for day in response.aggregations.visits_per_day.buckets:
            print(f"Date: {day.key_as_string} - Visits: {day.doc_count}")
        return response.aggregations.visits_per_day.buckets

    def total_ip(self):
        """
        汇总所有的ip
        :return:
        """
        s = Search(using=self.es, index=self.index)
        # 添加时间范围查询，限制为过去两周
        s = s.query('range', visit_time={'gte': self.two_weeks_ago_str})

        for ua in self.excluded_user_agents:
            s = s.query('bool', must_not=[Q("regexp", user_agent=ua)])
        # 定义日期直方图聚合，以visit_time字段进行按天聚合
        s.aggs.bucket(
            'visits_per_day',
            'date_histogram',
            field='visit_time',
            calendar_interval='day'
        ).bucket(
            'unique_ips',
            'cardinality',
            field='remote_addr'  # 确保这里使用了正确的IP字段名
        )

        # 执行查询
        response = s.execute()

        # 遍历聚合结果并打印每天的独立IP访问量
        for day in response.aggregations.visits_per_day.buckets:
            print(f"Date: {day.key_as_string} - Unique IPs: {day.unique_ips.value}")

        return response.aggregations.visits_per_day.buckets

    def google_ip(self):
        """
        统计所有来自Google的爬虫，不使用正则表达式进行匹配。
        """
        s = Search(using=self.es, index=self.index)

        # 添加时间范围查询，限制为过去两周
        s = s.query('range', visit_time={'gte': self.two_weeks_ago_str})

        # 使用match_phrase查询匹配包含"Googlebot"的用户代理字符串
        s = s.query('bool', must=[Q("match_phrase", user_agent="Googlebot")])

        # 定义日期直方图聚合，以visit_time字段进行按天聚合
        s.aggs.bucket(
            'visits_per_day',
            'date_histogram',
            field='visit_time',
            calendar_interval='day'
        )

        # 执行查询
        response = s.execute()

        # 遍历聚合结果并打印每天的总访问次数
        for day in response.aggregations.visits_per_day.buckets:
            print(f"Date: {day.key_as_string} - Googelbot: {day.doc_count}")

        return response.aggregations.visits_per_day.buckets


# ip聚合
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
