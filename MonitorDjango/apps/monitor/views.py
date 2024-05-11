from datetime import datetime, timedelta, date
import geoip2.database
from celery import chain
from django.db import transaction
from django.db.models import Count, Q, Avg, Sum, F
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.utils.dateparse import parse_date
from django.utils.timezone import make_aware
from pygrok import pygrok
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from utils.dns_parse import lookup_ip
from .es import IpAggregation, SpiderAggregation, TotalAggregation, WebsiteES
from .models import VisitModel, WebsiteModel, LogFileModel, UserSettingsModel, TotalModel, TotalDayModel, IPDayModel
from .serializer.monitor_serializer import MonitorSerializer, VisitSerializer, TotalSerializer, TotalDaySerializer
from .tasks import handle_uploaded_file_task, total_day, ip_day, nslookup
from django.http import JsonResponse
from celery.result import AsyncResult

pattern_string = r'(?P<remote_addr>\d+\.\d+\.\d+\.\d+) - - \[(?P<time_local>.+?)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>HTTP\/\d\.\d)" (?P<status>\d{3}) (?P<body_bytes_sent>\d+) "(?P<http_referer>[^"]*)" "(?P<user_agent>[^"]+)"'


def task_status(request, task_id):
    task_result = AsyncResult(task_id)
    return JsonResponse({'status': task_result.status, 'result': task_result.result})


def csrf_token(request):
    csrf = get_token(request)
    return JsonResponse({'csrfToken': csrf})


class UserSettingsAPIView(APIView):
    """
    # 用户设置修改
    """

    # permission_classes = [IsAuthenticated]

    def get(self, request):
        user_settings = UserSettingsModel.objects.filter(user=request.user).first()

        if not user_settings:
            data = {
                'user': request.user.username,
            }
            return Response(data, status=status.HTTP_200_OK)
        data = {
            'user': request.user.username,
            'nginx_log_format': user_settings.nginx_log_format,
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        user_settings = UserSettingsModel.objects.filter(user=request.user).first()
        if not user_settings:
            user_settings = UserSettingsModel(user=request.user)
        user_settings.nginx_log_format = request.data.get('nginxLogFormat')
        user_settings.save()
        return Response({'message': '用户设置修改成功'}, status=status.HTTP_200_OK)


class LogUpload(APIView):
    """
    上传日志文件
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # 修改为多个文件上传处理
        try:
            file_lst = self.request.FILES.getlist('upload_file')
            # file = self.request.FILES['upload_file']
            print(file_lst)
            for file in file_lst:
                domain = self.request.POST.get('website', None)

                with transaction.atomic():
                    # 保存文件
                    log_file = LogFileModel(
                        user=request.user,
                        upload_file=file,
                    )
                    log_file.save()

                log_file = LogFileModel.objects.get(id=log_file.id)
                file_name = log_file.upload_file.name
                file_path = f'/home/yuzai/Project/website-monitor-dev/MonitorDjango/media/{file_name}'
                user_settins = UserSettingsModel.objects.filter(user=request.user).first()
                if not user_settins:
                    return Response({'message': '请先设置nginx日志格式'}, status=status.HTTP_401_UNAUTHORIZED)
                nginx_format = user_settins.nginx_log_format
                user_id = log_file.user.id
                # 调用celery任务
                result = handle_uploaded_file_task.delay(nginx_format, file_path, user_id, domain)
                # handle_uploaded_file_task(nginx_format, file_path, user_id, domain)
                # 获取任务id
                task_id = result.id

            return Response({'message': '文件上传成功，正在后台处理',
                             'task_id': task_id
                             },
                            status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            print(e)
            return Response({'message': f'文件上传失败: {str(e)}'}, status=status.HTTP_404_NOT_FOUND)


class WebsiteListAPIView(APIView):
    """
    获取站点列表
    """

    permission_classes = [IsAuthenticated]

    def get_dates_range(self, dates):
        """根据传入的日期列表计算查询范围"""
        if not dates or len(dates) < 2:
            return None

        start_date = parse_date(dates[0].split('T')[0])
        end_date = parse_date(dates[1].split('T')[0])

        if start_date and end_date and start_date == end_date:
            # 包括结束日期当天的整天
            end_date += timedelta(days=1)

        return start_date, end_date

    def filter_queryset_by_dates(self, queryset, dates_range):
        """根据日期范围过滤查询集"""
        if dates_range:
            start_date, end_date = dates_range

            # print('222', queryset, start_date, end_date)
            queryset = queryset.filter(visitmodel__visit_time__range=(start_date, end_date))
            # print('1111', queryset)
        return queryset

    def get(self, request, *args, **kwargs):
        # print("当前用户：", request.user.id)
        # after_key = request.query_params.get('after_key[domain]', None)
        date_str = request.query_params.get('date')
        domain = request.query_params.get('search_text')
        domain_list = request.query_params.get('domain_list')
        if domain_list:
            # 将所有的域名返回
            domain_list = TotalDayModel.objects.filter(user=request.user).values('domain').distinct()
            return Response(domain_list, status=status.HTTP_200_OK)

        if date_str:
            # 格式化日期,只要日期部分
            date_format = datetime.fromisoformat(date_str.rstrip('Z'))
            date_only_str = date_format.date().isoformat()

        else:
            date_only_str = datetime.now().date().isoformat()

        if domain:
            total_day_query = TotalDayModel.objects.filter(domain=domain, user=request.user,
                                                           visit_date=date_only_str)
        else:
            # 从数据库中获取数据
            total_day_query = TotalDayModel.objects.filter(user=request.user, visit_date=date_only_str,
                                                           url_count__isnull=False)
        if not total_day_query:  # 如果数据库中没有当天的数据，就调用celery任务进行计算
            total_day.delay(request.user.id, date=date_only_str)

        # 调用序列化器
        total_day_serializer = TotalDaySerializer(total_day_query, many=True)

        return Response(total_day_serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        website_id = request.data.get('id', '')
        dates = request.data.get('dates')
        # print(f'dates: {dates}, website_id: {website_id}')
        dates_range = self.get_dates_range(dates)
        # print(f'dates_range: {dates_range}')
        # 仅对有必要的记录进行查询，避免全表扫描
        queryset = WebsiteModel.objects.filter(id=website_id,
                                               user=self.request.user) if website_id else WebsiteModel.objects.filter(
            user=self.request.user)
        queryset = self.filter_queryset_by_dates(queryset, dates_range)
        # 对 visitmodel__remote_addrr 进行去重计数以获得 IP 总数
        ip_totals = queryset.annotate(distinct_ip=Count('visitmodel__remote_addr', distinct=True))

        # 对整个查询集进行计数以获得访问总数
        visit_totals = queryset.annotate(total_visits=Count('visitmodel'))

        # 对 visitmodel__remote_addr 和 visitmodel__user_agent 的组合进行去重以获得唯一访客数
        visitor_totals = queryset.values('visitmodel__remote_addr',
                                         'visitmodel__user_agent').distinct().count()

        # 直接计算数据传输总量
        data_transfer_totals = queryset.aggregate(data_transfer_totals=Sum('visitmodel__data_transfer'))[
                                   'data_transfer_totals'] or 0

        # 由于前面的查询都是基于同一个 queryset，它们可以结合在一起执行，减少数据库访问次数
        aggregated_data = {
            'visitor_totals': visitor_totals,
            'ip_totals': ip_totals.first().distinct_ip if ip_totals.exists() else 0,
            'visit_totals': visit_totals.first().total_visits if visit_totals.exists() else 0,
            'data_transfer_totals': data_transfer_totals,
        }

        print(aggregated_data)
        # 由于聚合结果直接返回字典，所以不需要额外的处理就可以直接使用
        return Response(aggregated_data, status=status.HTTP_200_OK)


class WebsiteDetailAPIView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]

    # serializer_class = MonitorSerializer

    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        ip = request.query_params.get('ip')
        date_str = request.query_params.get('date')
        domain = request.query_params.get('domain')

        hit_list = []
        # print(f'ip: {ip}, domain: {domain}, date: {date_str}')
        # 调用es
        website_es = WebsiteES(index='visit_new', user_id=user_id)
        if ip and domain:
            googlebot_ip_detail = website_es.get_googlebot_ip_detail(ip=ip, domain=domain, date=date_str)
            # print(googlebot_ip_detail['hits']['hits'])
            for hit in googlebot_ip_detail['hits']['hits']:
                # print(hit['_source'])
                hit_list.append(hit['_source'])
            data = {
                'website_detail': hit_list,
            }
            print(len(data['website_detail']))
            return Response(data=data, status=status.HTTP_200_OK)
        elif ip:  # 根据ip查询
            # print('ip', ip)
            website_detail, new_last_sort_value = website_es.get_website_detail(ip=ip, date=date_str)
        elif domain:
            # 如果有domain参数，就根据domain查询，查找最近一个月的数据
            date_month_ago = datetime.now() - timedelta(days=30)
            total_day_query = TotalDayModel.objects.filter(domain=domain, user=request.user,
                                                           visit_date__gte=date_month_ago).order_by('visit_date')
            # 调用序列化器
            total_day_serializer = TotalDaySerializer(total_day_query, many=True)
            return Response(total_day_serializer.data, status=status.HTTP_200_OK)
        data = {
            'website_detail': website_detail,
            'new_last_sort_value': new_last_sort_value,
        }
        return Response(data=data, status=status.HTTP_200_OK)


class WebsiteDetailGoogleBotAPIView(APIView):
    """
    GoogleBot的详细信息
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, domain, *args, **kwargs):
        googlebot = request.query_params.get('google_bot', '')
        visit_date = request.query_params.get('visit_date', '')
        if not domain:
            return Response({'error': 'Domain not found'}, status=status.HTTP_404_NOT_FOUND)
        if googlebot:
            # 根据domain查询某天的GoogleBot数据
            ip_agg = IpAggregation(index='visit_new', domain=domain, user_id=request.user.id)
            googlebot_ip_data = ip_agg.get_ip_googlebot(visit_date=visit_date)
            for bucket in googlebot_ip_data:
                bucket['country'] = lookup_ip(bucket.key,
                                              '/home/yuzai/Project/website-monitor-dev/MonitorDjango/utils/GeoLite2-Country.mmdb')

            data = [{'ip': bucket.key, 'count': bucket.doc_count, 'country': bucket.country} for bucket in
                    googlebot_ip_data]
            return Response(data, status=status.HTTP_200_OK)

        # 根据domain查询最近一个月的GoogleBot数据
        date_month_ago = datetime.now() - timedelta(days=30)
        total_day_query = TotalDayModel.objects.filter(domain=domain, user=request.user,
                                                       visit_date__gte=date_month_ago).order_by('-visit_date')
        if not total_day_query:
            return Response({'error': 'GoogleBot not found'}, status=status.HTTP_404_NOT_FOUND)
        # 调用序列化器
        total_day_serializer = TotalDaySerializer(total_day_query, many=True)

        # 调用es
        return Response(total_day_serializer.data, status=status.HTTP_200_OK)


class ChartDataAPIView(APIView):
    """
    获取图表数据
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        website_id = request.GET.get('id', '')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)  # 包括今天在内的过去7天

        # 确保website_id对应的WebsiteModel存在
        if website_id and not WebsiteModel.objects.filter(id=website_id, user=self.request.user).exists():
            return Response({'error': 'Website not found'}, status=404)

        # 构建基础查询集
        queryset = VisitModel.objects.filter(visit_time__range=(start_date, end_date))
        if website_id:
            queryset = queryset.filter(site__id=website_id)

        # 按天分组，同时统计访问量和独立IP数量
        stats_per_day = queryset.annotate(day=TruncDay('visit_time')) \
            .values('day') \
            .annotate(visit_total=Count('id'), ip_total=Count('remote_addr', distinct=True)) \
            .order_by('day')

        # 将查询结果转换为字典以便快速访问
        stats_dict = {item['day'].strftime('%Y-%m-%d'): item for item in stats_per_day}

        # 生成过去7天的每一天，并填充缺失的数据
        data = {
            'labels': [],
            'visit_total': [],
            'ip_total': [],
        }
        for single_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
            date_str = single_date.strftime('%Y-%m-%d')
            data['labels'].append(date_str)
            if date_str in stats_dict:
                data['visit_total'].append(stats_dict[date_str]['visit_total'])
                data['ip_total'].append(stats_dict[date_str]['ip_total'])
            else:
                # 没有数据的日期填充为0
                data['visit_total'].append(0)
                data['ip_total'].append(0)

        return Response(data, status=status.HTTP_200_OK)


class IpListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def to_serializer(self, ip_aggregation):
        return [{'ip': bucket.key, 'count': bucket.doc_count} for bucket in ip_aggregation]

    def get_ip_data(self, aggregation, date_str=None, time_window=None):
        ips_aggregation = self.to_serializer(aggregation)
        for ip_data in ips_aggregation:
            ip_data['country'] = lookup_ip(ip_data['ip'])
        return ips_aggregation

    def parse_date(self, date_str):
        """尝试解析日期字符串，返回日期对象或错误响应。"""
        try:
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ').date()
        except ValueError:
            return Response({'error': 'Invalid date format, please use YYYY-MM-DDTHH:MM:SS.sssZ'},
                            status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        domain = request.GET.get('domain', '')
        user_id = request.user.id
        date_str = request.query_params.get('date', '')
        check = request.query_params.get('check', '')
        day = self.parse_date(date_str)

        if isinstance(day, Response):
            return day  # 早退，如果日期解析失败

        print('check', check)
        if check == 'true':
            result = ip_day.delay(user_id, date=day.strftime("%Y-%m-%d"))
            # print(result)
            print('检测数据中...')
            return Response({'message': '数据处理中，请稍后刷新页面'},
                            status=status.HTTP_202_ACCEPTED)

        ip_queryset = IPDayModel.objects.filter(user=request.user, visit_date=day)

        # 如果数据库中没有当天的数据，就调用celery任务进行计算
        if not ip_queryset.exists():
            # 使用任务链
            # result = chain(ip_day.s(user_id, date=day.strftime("%Y-%m-%d")),
            #                nslookup.si(user_id, date=day.strftime("%Y-%m-%d"))).apply_async()
            result = ip_day.delay(user_id, date=day.strftime("%Y-%m-%d"))
            print(result)
            # print('1111')
            return Response({'message': '数据处理中，请稍后刷新页面'},
                            status=status.HTTP_202_ACCEPTED)

        date_week = day - timedelta(days=7)
        queryset_week = IPDayModel.objects.filter(user=request.user, visit_date__gte=date_week,
                                                  visit_date__lte=day).values('ip').annotate(
            count=Sum('count')).order_by('-count')
        queryset_day = IPDayModel.objects.filter(user=request.user, visit_date=day).values('ip').annotate(
            count=Sum('count')).order_by('-count')

        ip_aggre = IpAggregation(index='visit_new', domain=domain, user_id=user_id) if domain else IpAggregation(
            index='visit_new', user_id=user_id)

        data = {
            'ips_week_googlebot': list(queryset_week.filter(status=1).values('ip', 'count', 'country')[:100]),
            'ips_week_not_googlebot': list(queryset_week.exclude(status=1).values('ip', 'count', 'country')[:100]),
            'ips_day_googlebot': list(queryset_day.filter(status=1).values('ip', 'count', 'country')[:100]),
            'ips_day_not_googlebot': list(queryset_day.exclude(status=1).values('ip', 'count', 'country')[:100]),
            # 'ips_all': self.get_ip_data(ip_aggre.get_ip_aggregation()),
            # 'ips_day': self.get_ip_data(ip_aggre.get_ip_aggregation_by_date(date=day)),
            'ips_hour': self.get_ip_data(ip_aggre.get_ip_aggregation_time_window(date_str, 'hour', 1)),
            'ips_min': self.get_ip_data(ip_aggre.get_ip_aggregation_time_window(date_str, 'minute', 5)),
        }

        return Response(data, status=status.HTTP_200_OK)


class SpiderAPIView(APIView):
    """
    爬虫的统计
    """
    permission_classes = [IsAuthenticated]

    @staticmethod
    def get_object(pk, user):
        try:
            website = WebsiteModel.objects.get(pk=pk)
            return website
        except VisitModel.DoesNotExist:
            return

    def get(self, request, pk, *args, **kwargs):
        website = self.get_object(pk=pk, user=self.request.user)
        spider_aggregation = SpiderAggregation(index='visit_new', domain=website.domain)
        get_spider_aggregatio = spider_aggregation.get_spider_aggregation()
        # print(get_spider_aggregatio)
        return Response(list(get_spider_aggregatio), status=status.HTTP_200_OK)


class TotalAPIView(APIView):
    """
    汇总数据
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        # 获取当天日期
        today = date.today()
        # 获取过去两周的时间
        two_weeks_ago = today - timedelta(days=14)
        # 获取过去两周的数据
        total = TotalModel.objects.filter(user=user, visit_date__range=(two_weeks_ago, today))
        data = TotalSerializer(total, many=True).data
        # total_agg = TotalAggregation(index='visit_new', user_id=user.id)
        # es_total_visit = total_agg.total_visit()

        return Response(data, status=status.HTTP_200_OK)
