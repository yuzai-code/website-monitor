import logging
import re
import gzip
import tempfile
from datetime import datetime, timedelta

from django.db.models import Count, Q, Avg, Sum, F
from django.db.models.functions import TruncDay
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.utils.dateparse import parse_date
from pygrok import pygrok
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .es import Aggregation, SpiderAggregation, TotalIPVisit
from .models import VisitModel, WebsiteModel, LogFileModel
from .serializer.monitor_serializer import MonitorSerializer, VisitSerializer
from .tasks import handle_uploaded_file_task
from django.http import JsonResponse
from celery.result import AsyncResult

pattern_string = r'(?P<remote_addr>\d+\.\d+\.\d+\.\d+) - - \[(?P<time_local>.+?)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>HTTP\/\d\.\d)" (?P<status>\d{3}) (?P<body_bytes_sent>\d+) "(?P<http_referer>[^"]*)" "(?P<user_agent>[^"]+)"'


def task_status(request, task_id):
    task_result = AsyncResult(task_id)
    return JsonResponse({'status': task_result.status, 'result': task_result.result})


def csrf_token(request):
    csrf = get_token(request)
    print('11111------------', csrf)
    return JsonResponse({'csrfToken': csrf})


def index(request):
    website = WebsiteModel.objects.all()
    context = {'website': website}
    return render(request, 'index.html', context)


def nginx_logs(request):
    # 获取所有的访问信息
    visits = VisitModel.objects.all()
    # 将数据传递给模板
    context = {'visits': visits}
    return render(request, 'nginx_logs.html', context)


class LogUpload(APIView):
    """
    上传日志文件
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            file = self.request.FILES['upload_file']
            domain = self.request.POST.get('website', None)
            nginx_format = self.request.POST.get('nginx_log_format')

            # 保存文件
            log_file = LogFileModel(
                user=request.user,
                upload_file=file,
                nginx_log_format=nginx_format,
            )
            log_file.save()

            # 调用celery任务
            result = handle_uploaded_file_task.delay(log_file.id, domain)
            # handle_uploaded_file_task(log_file.id, domain)
            # 获取任务id
            task_id = result.id

            return Response({'message': '文件上传成功，正在后台处理',
                             'task_id': task_id
                             },
                            status=status.HTTP_202_ACCEPTED)
        except Exception as e:
            print(e)
            return Response({'message': f'文件上传失败: {str(e)}'}, status=400)


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

            print('222', queryset, start_date, end_date)
            queryset = queryset.filter(visitmodel__visit_time__range=(start_date, end_date))
            print('1111', queryset)
        return queryset

    def get(self, request, *args, **kwargs):
        print("当前用户：", request.user.id)
        queryset = WebsiteModel.objects.filter(user_id=request.user.id)
        print(queryset)
        need_nested = request.query_params.get('need_nested', 'false').lower() in ['true', '1', 'yes']
        search_text = request.query_params.get('search', '')
        if search_text:
            # 模糊查询内容
            queryset = queryset.filter(domain__icontains=search_text)
            print(queryset)
            serializer = MonitorSerializer(queryset, many=True)
            return Response(serializer.data, 200)
        # 接收input参数，而不是fields
        input_fields = request.query_params.get('input')
        if input_fields:
            input_fields = input_fields.split(',')

        context = {
            'need_nested': need_nested,
            'request': request,
        }

        # 传递input_fields给序列化器
        serializer = MonitorSerializer(queryset, many=True, context=context,
                                       fields=input_fields if input_fields else None)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        website_id = request.data.get('id', '')
        dates = request.data.get('dates')
        print(f'dates: {dates}, website_id: {website_id}')
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
    serializer_class = MonitorSerializer

    def get_queryset(self):
        """只返回当前用户的数据"""
        return WebsiteModel.objects.filter(user=self.request.user)

    def get_serializer_context(self):
        context = super(WebsiteDetailAPIView, self).get_serializer_context()
        context.update({'need_nested': True})  # 设置 need_nested
        return context


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

    @staticmethod
    def get_object(pk, user):
        try:
            website = WebsiteModel.objects.get(pk=pk, user=user)
            return website
        except WebsiteModel.DoesNotExist:
            return

    def to_serializer(self, ip_aggregation):
        ips_data = [{'key': bucket.key, 'doc_count': bucket.doc_count} for bucket in ip_aggregation]
        return ips_data

    def get(self, request, pk):
        obj = self.get_object(pk, user=self.request.user)
        if not obj:
            return Response(data={"msg": "没有此域名信息"}, status=status.HTTP_404_NOT_FOUND)

        # 调用es聚合查询所有ip的数量
        aggre = Aggregation(index='visit', domain=obj.domain, user_id=self.request.user.id)
        ips_aggregation_all = aggre.get_ip_aggregation()
        ips_all = self.to_serializer(ips_aggregation_all)

        # 查询过去5分钟内ip数量最多的前10个
        ips_aggregation_min = aggre.get_10_ip_aggregation_min()
        ips_min = self.to_serializer(ips_aggregation_min)

        # 查询过去1小时内ip数量最多的前10个
        ips_aggregation_hour = aggre.get_10_ip_aggregation_hour()
        ips_hour = self.to_serializer(ips_aggregation_hour)

        # 查询过去1天内ip数量最多的前10个
        ips_aggregation_day = aggre.get_10_ip_aggregation_day()
        ips_day = self.to_serializer(ips_aggregation_day)
        print(ips_aggregation_day)

        data = {
            'ips_all': ips_all,
            'ips_min': ips_min,
            'ips_hour': ips_hour,
            'ips_day': ips_day
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
        spider_aggregation = SpiderAggregation(index='visit', domain=website.domain)
        get_spider_aggregatio = spider_aggregation.get_spider_aggregation()
        print(get_spider_aggregatio)
        return Response(list(get_spider_aggregatio), status=status.HTTP_200_OK)


class TotalIpVisit(APIView):
    """
    统计所有的ip和访问量
    """
    permission_classes = [IsAuthenticated]

    def to_serailizer(self, es_data):
        date = []
        count = []
        for bucket in es_data:
            date_str = bucket.key_as_string
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            formatted_date = date_obj.strftime("%Y-%m-%d")
            date.append(formatted_date)
            count.append(bucket.doc_count)

        return date, count

    def get(self, request):
        total = TotalIPVisit(index='visit', user_id=self.request.user.id)
        visit_date, visit_count = self.to_serailizer(total.total_visit())
        es_ips = total.total_ip()
        ip_date = [bucket.key_as_string for bucket in es_ips]
        ip_count = [bucket.unique_ips.value for bucket in es_ips]
        es_google_ips = total.google_ip()
        dates = [bucket.key_as_string for bucket in es_google_ips]
        google_ips_counts = [bucket.doc_count for bucket in es_google_ips]

        # print(visit_count, ip_count, google_ips)
        data = {
            'date': visit_date,
            'visit_count': visit_count,
            'ip_date': ip_date,
            'ip_count': ip_count,
            'google_ips': google_ips_counts,
        }
        print(data)
        return Response(data, status=status.HTTP_200_OK)
