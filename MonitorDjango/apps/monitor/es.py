from datetime import datetime, timedelta

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A
from WebsiteMonitor.settings import config


class ElasticsearchQueryHelper:
    def __init__(self, index='visit_new', user_id=None):
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

    def execute_search(self, search):
        return search.execute()


class SpiderAggregation:
    """
    爬虫聚合
    """

    def __init__(self, index, domain, user_id):
        self.index = index
        self.user_id = user_id
        self.helper = ElasticsearchQueryHelper(index=index, user_id=user_id)
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
        self.helper = ElasticsearchQueryHelper(index=index, user_id=user_id)
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

        s = s.query("wildcard", http_referer="*google.com*")

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
        # for day in response.aggregations.visits_per_day.buckets:
        #     print(f"Date: {day.key_as_string} - Visits: {day.doc_count}")
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
        # for day in response.aggregations.visits_per_day.buckets:
        #     print(f"Date: {day.key_as_string} - Unique IPs: {day.unique_ips.value}")

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
        s = s.query("wildcard", user_agent="*googlebot*")

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
        # for day in response.aggregations.visits_per_day.buckets:
        # print(f"Date: {day.key_as_string} - Googelbot: {day.doc_count}")

        return response.aggregations.visits_per_day.buckets


# ip聚合
class IpAggregation:
    def __init__(self, index, domain=None, user_id=None):
        self.index = index
        self.user_id = user_id
        self.helper = ElasticsearchQueryHelper(index=index, user_id=user_id)
        self.es = Elasticsearch([f"http://{config['es']['ES_URL']}"])
        self.domain = domain

    def get_ip_aggregation(self, size=None):
        """
        ip访问次数最多的前15个
        :param size:
        :return:
        """
        s = Search(using=self.es, index=self.index)
        s = s.query("bool", must_not=[
            Q("wildcard", user_agent="*Googlebot*"),
            Q("wildcard", user_agent="*neobot*"),
            Q("wildcard", user_agent="python*"),
        ])
        s = s.query("bool", must_not=[
            Q("wildcard", path=".*/static/*."),
        ])

        # 如果有指定域名，则添加域名过滤
        if self.domain:
            s = s.filter('term', domain__keyword=self.domain)
            s = self.helper.filter_by_user_id(s)
            s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
            response = s.execute()
            return response.aggregations.ip.buckets
        s = self.helper.filter_by_user_id(s)
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        print('1111111')
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_ip_aggregation_by_date(self, date):
        # 获取指定日期内ip数量最多的前15个
        s = Search(using=self.es, index=self.index)
        s = self.helper.filter_by_user_id(s)

        s = s.query('bool',
                    must_not=[
                        Q("wildcard", user_agent="*Googlebot*"),
                        Q("wildcard", user_agent="*neobot*"),
                        Q("term", user_agent="python-requests/2.31.0"),
                    ])
        s = s.query(
            "bool", must_not=[
                Q("wildcard", path="*/static/*"),
                Q("wildcard", path="*/media/*"),
                Q("wildcard", path="*/favicon.ico")
            ]
        )

        # 将时间范围过滤调整为指定日期
        start_date = date + 'T00:00:00'  # 指定日期的 00:00:00
        end_date = date + 'T23:59:59'  # 指定日期的 23:59:59
        s = s.filter('range', **{'visit_time': {'gte': start_date, 'lte': end_date}})
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets

    def get_10_ip_aggregation_min(self):
        # 获取过去5分钟内ip数量最多的前10个
        s = Search(using=self.es, index=self.index)
        s = s.filter('term', domain__keyword=self.domain)
        s = self.helper.filter_by_user_id(s)
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
        s = self.helper.filter_by_user_id(s)
        s = s.filter('range', **{'visit_time': {'gte': 'now-1h', 'lte': 'now'}})
        s.aggs.bucket('ip', 'terms', field='remote_addr', size=15)
        response = s.execute()
        return response.aggregations.ip.buckets


def search_ip(self, ip, size=None):
    # 根据ip查询
    s = Search(using=self.es, index=self.index)
    s = self.helper.filter_by_user_id(s)
    s = s.query(Q('term', domain__keyword=self.domain) & Q('term', remote_addr=ip))
    response = s.execute()
    return response


class WebsiteES(ElasticsearchQueryHelper):
    """
    网站列表
    """

    def __init__(self, index, user_id):
        super().__init__(index=index, user_id=user_id)

    def get_website_list(self, domain=None, page_size=1000, after_key=None):
        """
        获取网站列表
        :param page: 当前页码
        :param page_size: 每页数据量
        :param after_key: 用于composite aggregation的分页键
        :return: 当前页的网站列表数据和下一页的键
        """
        data_list = []
        search = self.search
        # search = search.exclude("match", user_agent="neobot")
        # search = search.exclude("match", user_agent="Googlebot")
        # search = search.exclude("match", path="*/static/*")
        # search = search.exclude("match", path="*/media/*")
        # search = search.exclude("match", path="*/favicon.ico")

        search = self.filter_by_user_id(search)

        if domain:
            wildcard_query = Q("wildcard", domain__keyword=f'*{domain}*')
            search = search.query('bool', must=[wildcard_query])
        print(search.to_dict())
        # 使用Composite Aggregation
        composite_agg = {
            "sources": [
                {"domain": {"terms": {"field": "domain.keyword"}}}
            ],
            "size": page_size
        }

        if after_key:
            composite_agg['after'] = after_key  # 用于继续从上一次的最后位置开始
        print('1111', after_key)
        search.aggs.bucket('by_domain', 'composite', **composite_agg) \
            .metric('ips', 'cardinality', field='remote_addr') \
            .metric('data_transfers', 'sum', field='data_transfer')

        response = self.execute_search(search)

        # 获取聚合结果
        aggs = response.aggregations.by_domain

        for bucket in aggs.buckets:
            domain = bucket.key.domain
            ips = bucket.ips.value
            data_transfers = bucket.data_transfers.value
            data_list.append({
                'domain': domain,
                'ips': ips,
                'data_transfers': data_transfers,
                'visits': bucket.doc_count,
            })

        # 检查是否有更多页
        after_key = aggs.after_key if 'after_key' in aggs else None
        # print('222', after_key)
        return data_list, after_key

    def get_website_detail(self, domain=None, ip=None, last_sort_value=None, page_size=1000):
        data_list = []
        search = self.search
        search = self.filter_by_user_id(search)

        if domain:
            search = search.filter('term', domain__keyword=domain)
        elif ip:
            search = search.filter('term', remote_addr=ip)

        # 确保查询结果按照某个字段排序，这里假设是 'timestamp'
        search = search.sort({'visit_time': {'order': 'desc'}})

        # 设置每页的大小
        search = search.extra(size=page_size)

        # 如果提供了 last_sort_value，使用它来获取下一页数据
        if last_sort_value:
            search = search.extra(search_after=[last_sort_value])

        # 执行搜索
        response = self.execute_search(search)

        # 收集数据和新的 last_sort_value
        new_last_sort_value = None
        for hit in response:
            data_list.append(hit.to_dict())
            if 'sort' in hit:
                new_last_sort_value = hit['sort'][0]

        return data_list, new_last_sort_value
