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

    def exclude_filter(self, search):
        """
        排除爬虫和静态资源
        :param search:
        :return:
        """
        search = search.query('bool', must_not=[Q("wildcard", user_agent="*googlebot*"),
                                                Q("wildcard", user_agent="*bingbot*"),
                                                Q("wildcard", user_agent="*neobot*"),
                                                Q("wildcard", path="*woff*"),
                                                Q("wildcard", path="*.js"),
                                                Q("wildcard", path="*.jpg"),
                                                Q("wildcard", path="*.png"),
                                                Q("wildcard", path="*.css"),
                                                Q("wildcard", path="*.json"),
                                                Q("wildcard", path="*.ico"),
                                                Q("wildcard", path="*.svg"),
                                                Q("wildcard", path="*.js.php"),
                                                ])
        return search

    def filter_by_user_id(self, search):
        if self.user_id:
            search = search.filter('term', user_id=self.user_id)
        return search

    def filter_by_domain(self, search, domain=None):
        if domain:
            search = search.filter('term', domain__keyword=domain)
        return search

    def execute_search(self, search):
        """
        执行搜索并处理错误
        """
        try:
            response = search.execute()
            return response.aggregations.ip.buckets
        except Exception as e:
            print(f"Failed to execute search: {e}")
            return []


class SpiderAggregation(ElasticsearchQueryHelper):
    """
    统计常见的爬虫访问情况
    """

    def __init__(self, index, user_id):
        super().__init__(index=index, user_id=user_id)
        self.included_user_agents = [
            "*Googlebot*",  # goolebot
            "*bingbot*",  # bingbot
        ]


class TotalAggregation(ElasticsearchQueryHelper):
    """
    汇总,统计过去两周内的数据
    """

    def __init__(self, index, user_id):
        super().__init__(index=index, user_id=user_id)
        # 初始化方法，设置指定的索引和用户ID，并计算两周前的日期
        self.two_weeks_ago = datetime.now() - timedelta(weeks=2)  # 计算两周前的日期)
        self.two_weeks_ago_str = self.two_weeks_ago.strftime('%Y-%m-%dT%H:%M:%S')  # 转换为适合Elasticsearch的日期格式字符串)
        self.excluded_user_agents = [
            "*Googlebot*",  # 爬虫
            "*bingbot*",
        ]
        self.included_user_agents = "compatible; Googlebot/2.1; +http://www.google.com/bot.html",

    def total_visit(self):
        """
        统计过去两周内的总访问量
        :return: 返回过去两周内按天统计的访问量数据
        """
        s = Search(using=self.es, index=self.index)
        s = self.filter_by_user_id(s)
        # 排除爬虫和指定文件类型
        s = self.exclude_filter(s)
        # 添加时间范围查询，限制为过去两周
        s = s.query('range', visit_time={'gte': self.two_weeks_ago_str})

        # 按天进行聚合统计
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
        response = s.execute()
        return response.aggregations.visits_per_day.buckets

    def google_visit(self):
        """
        统计过去两周内，排除特定用户代理后的每日访问量。
        """

        static_paths = [
            Q("wildcard", path="*/static/*"),
            Q("wildcard", path="*/media/*"),
        ]

        # 创建搜索对象
        s = Search(using=self.es, index=self.index)
        s = self.filter_by_user_id(s)

        s = s.query("wildcard", http_referer="*google.com*")

        s = s.query('range', visit_time={'gte': self.two_weeks_ago_str})

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
        s = self.filter_by_user_id(s)
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

    def google_bot(self):
        """
        统计所有来自Google的爬虫，不使用正则表达式
        Q("wildcard), user_agent={"*Bingbot*进行匹配,。
        """
        s = Search(using=self.es, index=self.index)

        s = self.filter_by_user_id(s)
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
class IpAggregation(ElasticsearchQueryHelper):
    def __init__(self, index, user_id, domain=None):
        super().__init__(index=index, user_id=user_id)
        self.domain = domain

    def _base_search(self, additional_filters=None):
        """
        创建一个基本的搜索查询，排除了一些常见的机器人访问和静态资源访问
        """
        search_query = Search(using=self.es, index=self.index)
        search_query = self.exclude_filter(search_query)
        if self.domain:
            search_query = search_query.filter('term', domain__keyword=self.domain)

        if self.user_id:
            search_query = self.filter_by_user_id(search_query)

        if additional_filters:
            for filt in additional_filters:
                search_query = search_query.filter('range', **filt)

        return search_query

    def get_ip_aggregation(self, size=15):
        """
        获取IP访问次数最多的前N个
        """
        search_query = self._base_search()
        search_query.aggs.bucket('ip', 'terms', field='remote_addr', size=size)
        return self.execute_search(search_query)

    def get_ip_aggregation_by_date(self, date, size=15):
        """
        获取指定日期内IP数量最多的前N个
        """
        filters = [{
            'visit_time': {
                'gte': f'{date}T00:00:00',
                'lte': f'{date}T23:59:59'
            }
        }]
        search_query = self._base_search(additional_filters=filters)
        search_query.aggs.bucket('ip', 'terms', field='remote_addr', size=size)
        return self.execute_search(search_query)

    def get_ip_aggregation_time_window(self, from_time, time_unit, duration, size=10):
        """
        获取从指定时间开始，指定时间单位和持续时长内IP数量最多的前N个
        """
        from_time = datetime.strptime(from_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        if time_unit == "minute":
            to_time = from_time + timedelta(minutes=duration)
        elif time_unit == "hour":
            to_time = from_time + timedelta(hours=duration)
        else:
            raise ValueError("Unsupported time unit. Use 'minute' or 'hour'.")

        filters = [{
            'visit_time': {
                'gte': from_time.isoformat(),
                'lte': to_time.isoformat()
            }
        }]

        search_query = self._base_search(additional_filters=filters)
        search_query.aggs.bucket('ip', 'terms', field='remote_addr', size=size)
        return self.execute_search(search_query)


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
        search = self.filter_by_user_id(search)

        if domain:
            wildcard_query = Q("wildcard", domain__keyword=f'*{domain}*')
            search = search.query('bool', must=[wildcard_query])
        # print(search.to_dict())
        # 使用Composite Aggregation
        composite_agg = {
            "sources": [
                {"domain": {"terms": {"field": "domain.keyword"}}}
            ],
            "size": page_size
        }

        if after_key:
            print('1111')
            composite_agg['after'] = after_key  # 用于继续从上一次的最后位置开始
        # print('1111', after_key)
        search.aggs.bucket('by_domain', 'composite', **composite_agg) \
            .metric('ips', 'cardinality', field='remote_addr') \
            .metric('data_transfers', 'sum', field='data_transfer')

        response = search.execute()

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

        after_key = getattr(aggs, 'after_key', None)
        # print('222', after_key)
        return data_list, after_key

    def get_website_detail(self, domain=None, ip=None, last_sort_value=None, date=None, page_size=1000):
        data_list = []
        search = self.search
        search = self.filter_by_user_id(search)

        search = self.exclude_filter(search)
        if domain:
            search = search.filter('term', domain__keyword=domain)
        elif ip:
            search = search.filter('term', remote_addr=ip)

        if date:
            date = date.split(' ')[0]
            print(date)
            search = search.filter('range', visit_time={'gte': f'{date}T00:00:00', 'lte': f'{date}T23:59:59'})
        # 确保查询结果按照某个字段排序，这里假设是 'timestamp'
        search = search.sort({'visit_time': {'order': 'desc'}})

        # 设置每页的大小
        search = search.extra(size=page_size)

        # 如果提供了 last_sort_value，使用它来获取下一页数据
        if last_sort_value:
            search = search.extra(search_after=[last_sort_value])
        # 执行搜索
        response = search.execute()

        # 收集数据和新的 last_sort_value
        new_last_sort_value = None
        for hit in response:
            data_list.append(hit.to_dict())
            if 'sort' in hit:
                new_last_sort_value = hit['sort'][0]

        return data_list, new_last_sort_value
