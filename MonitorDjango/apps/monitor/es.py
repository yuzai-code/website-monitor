from datetime import datetime, timedelta

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A
from WebsiteMonitor.settings import config


class ElasticsearchQueryHelper:
    def __init__(self, index='visit', user_id=None):
        self.index = index
        self.user_id = user_id
        self.es = Elasticsearch([f"http://{config['es']['ES_URL']}"])
        self.search = Search(using=self.es, index=self.index)

    def filter_by_user_id(self, search):
        if self.user_id:
            search = search.filter('term', user_id=self.user_id)
        return search

    def filter_by_domain(self, search, domain=None):
        if domain:
            search = search.filter('term', domain__keyword=domain)
        return search

    def aggregate_by_field(self, search, field, agg_name='aggregation', size=15, ):
        search.aggs.bucket(agg_name, 'terms', field=field, size=size)
        return search

    def execute_search(self, search):
        return search.execute()


class SpiderAggregation:
    """
    爬虫聚合
    """

    def __init__(self, index, domain, user_id):
        self.index = index
        self.user_id = user_id
        self.helper = ElasticsearchQueryHelper(index=index)
        self.es = Elasticsearch([f"http://{config['es']['ES_URL']}"])
        self.domain = domain

    def get_spider_aggregation(self, remote_addr):
        # 创建一个查询实例，指定使用的Elasticsearch实例和索引
        s = Search(using=self.es, index=self.index)
        s = self.helper.filter_by_user_id(s)
        response = s.execute()
        return response.aggregations.ip.buckets


# 统计总的IP与访问量
class TotalIPVisit:

    def __init__(self, index, user_id):
        self.index = index
        self.user_id = user_id
        self.helper = ElasticsearchQueryHelper(index=index)
        self.es = Elasticsearch([f"http://{config['es']['ES_URL']}"])
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
        s = self.helper.filter_by_user_id(s)

        s = s.query("match", http_referer="google.com")

        s = s.query('range', visit_time={'gte': self.two_weeks_ago_str})
        # # 构建排除特定用户代理和静态文件路径的查询
        # excluded_queries = [Q("regexp", user_agent=ua) for ua in self.excluded_user_agents] + static_paths
        #
        # # 添加排除用户代理为空的条件
        # excluded_queries.append(~Q("exists", field="user_agent"))

        # 添加时间范围查询，限制为过去两周
        # date_range_query = Q('range', visit_time={'gte': self.two_weeks_ago_str})

        # 将查询条件组合起来
        # query = Q('bool', must=[date_range_query], must_not=excluded_queries)
        # query = Q('bool', must=[date_range_query])

        # 添加查询
        # s = s.query(query)

        # 定义日期直方图聚合，以visit_time字段进行按天聚合
        s.aggs.bucket(
            'visits_per_day',
            'date_histogram',
            field='visit_time',
            calendar_interval='day',
            min_doc_count=0,
            extended_bounds={
                "min": self.two_weeks_ago_str,
                "max": datetime.now().strftime('%Y-%m-%dT%H:%M:%S')  # 使用当前时间作为结束时间
            }
        )

        # 执行查询
        response = s.execute()
        # print(response)
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
        s = self.helper.filter_by_user_id(s)
        # 添加时间范围查询，限制为过去两周
        s = s.query('range', visit_time={'gte': self.two_weeks_ago_str})

        # s = s.query('match', user_agent='Googlebot')

        # for ua in self.excluded_user_agents:
        #     s = s.query('bool', must_not=[Q("regexp", user_agent=ua)])
        # 定义日期直方图聚合，以visit_time字段进行按天聚合
        s.aggs.bucket(
            'visits_per_day',
            'date_histogram',
            field='visit_time',
            calendar_interval='day',
            min_doc_count=0,
            extended_bounds={
                "min": self.two_weeks_ago_str,
                "max": datetime.now().strftime('%Y-%m-%dT%H:%M:%S')  # 使用当前时间作为结束时间
            }
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

        s = self.helper.filter_by_user_id(s)
        # 添加时间范围查询，限制为过去两周
        s = s.query('range', visit_time={'gte': self.two_weeks_ago_str})

        # 使用match_phrase查询匹配包含"Googlebot"的用户代理字符串
        # s = s.query('bool', must=[Q("match_phrase", user_agent="Googlebot")])
        s = s.query("match", user_agent="Googlebot")

        # 定义日期直方图聚合，以visit_time字段进行按天聚合
        s.aggs.bucket(
            'visits_per_day',
            'date_histogram',
            field='visit_time',
            calendar_interval='day',
            min_doc_count=0,
            extended_bounds={
                "min": self.two_weeks_ago_str,
                "max": datetime.now().strftime('%Y-%m-%dT%H:%M:%S')  # 使用当前时间作为结束时间
            }
        )

        # 执行查询
        response = s.execute()

        # 遍历聚合结果并打印每天的总访问次数
        for day in response.aggregations.visits_per_day.buckets:
            print(f"Date: {day.key_as_string} - Googelbot: {day.doc_count}")

        return response.aggregations.visits_per_day.buckets


# ip聚合
class Aggregation:
    def __init__(self, index, domain=None, user_id=None):
        self.index = index
        self.user_id = user_id
        self.helper = ElasticsearchQueryHelper(index=index)
        self.es = Elasticsearch([f"http://{config['es']['ES_URL']}"])
        self.domain = domain

    def get_ip_aggregation(self, size=None):
        # 聚合ip查询
        s = Search(using=self.es, index=self.index)

        if self.domain:
            s = s.filter('term', domain__keyword=self.domain)
        s = self.helper.filter_by_user_id(s, self.user_id)
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_min(self):
        # 获取过去5分钟内ip数量最多的前10个
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        s = self.helper.filter_by_user_id(s, self.user_id)
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
        s = self.helper.filter_by_user_id(s, self.user_id)
        s = s.filter('range', **{'visit_time': {'gte': 'now-1h', 'lte': 'now'}})
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_day(self):
        # 获取今天一天内ip数量最多的前10各
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        s = self.helper.filter_by_user_id(s, self.user_id)
        # 将时间范围过滤调整为过去24小时  # todo 之后可以使用@timestamp
        s = s.filter('range', **{'visit_time': {'gte': 'now-24h/h', 'lte': 'now/h'}})
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def search_ip(self, ip, size=None):
        # 根据ip查询
        s = Search(using=self.es, index=self.index)
        s = self.helper.filter_by_user_id(s, self.user_id)
        s = s.query(Q('term', domain__keyword=self.domain) & Q('term', remote_addr=ip))
        response = s.execute()
        return response


class WebsiteListES(ElasticsearchQueryHelper):
    """
    网站列表
    """

    def __init__(self, index, user_id):
        super().__init__(index=index, user_id=user_id)

    def get_website_list(self):
        """
        获取网站列表
        :return:
        """
        search = self.search
        search = search.exclude("match", user_agent="neobot")
        search = search.exclude("match", path="*/static/*")
        # 使用聚合计算每个网站的访问量、访客量和 IP 数
        search.aggs.bucket('websites', 'terms', field='domain')
        search.aggs['websites'].metric('visitor_total', 'cardinality', field='remote_addr')
        search.aggs['websites'].metric('ip_total', 'cardinality', field='remote_addr')
        search.aggs['websites'].metric('visit_total', 'cardinality', field='visit_time')
        search.aggs['websites'].metric('data_transfer_total', 'sum', field='data_transfer')
        # search.aggs['websites'].bucket('error_count', 'filter', {'match': {'status_code': 404}}).metric('error_count',
        #                                                                                                 'value_count')

        # search.aggs['websites'].metric('malicious_request_total', 'value_count', field='malicious_request')

        # 执行查询
        response = search.execute()

        # 提取聚合结果
        website_statistics = []
        for website_bucket in response.aggregations.websites.buckets:
            website_stats = {
                'domain': website_bucket.key,
                'visit_total': website_bucket.visit_total.value,
                'visitor_total': website_bucket.visitor_total.value,
                'ip_total': website_bucket.ip_total.value,
                'data_transfer_total': website_bucket.data_transfer_total.value,
                # 'error_total': website_bucket.error_count.error_count.value,
                # 'malicious_request_total': website_bucket.malicious_request_total.value
            }
            website_statistics.append(website_stats)

        return website_statistics
