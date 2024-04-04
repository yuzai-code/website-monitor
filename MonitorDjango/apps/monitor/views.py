import logging
import re
import gzip
import tempfile
from datetime import datetime, timedelta

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Count, Q, Avg, Sum, F
from django.db.models.functions import TruncDay
from django.forms import model_to_dict
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render, redirect
from django.utils.dateparse import parse_date
from django.views.generic import CreateView, DetailView, ListView
from pygrok import pygrok
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .es import Aggregation
from .forms import LogFileForm
from .models import VisitModel, WebsiteModel, LogFileModel
from .serializer.monitor_serializer import MonitorSerializer, VisitSerializer

pattern_string = r'(?P<remote_addr>\d+\.\d+\.\d+\.\d+) - - \[(?P<time_local>.+?)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>HTTP\/\d\.\d)" (?P<status>\d{3}) (?P<body_bytes_sent>\d+) "(?P<http_referer>[^"]*)" "(?P<user_agent>[^"]+)"'


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


class LogUpload(CreateView):
    """
    上传日志文件
    """
    model = LogFileModel
    form_class = LogFileForm
    template_name = 'logs/upload.html'

    def post(self, request, *args, **kwargs):
        # print('111')
        try:
            file = self.request.FILES['upload_file']
            domain = self.request.POST.get('website', None)
            nginx_format = self.request.POST.get('nginx_log_format')
            # print('sdasda')
            # file = request.FILES.get('upload_file')
            # domain = request.POST.get('website', '')
            # nginx_format = request.POST.get('nginx_log_format', '')
            print(f'file: {file}, domain:{domain},nginx_format:{nginx_format}')
            file_name = file.name
            if domain.strip() == '':
                self.handle_uploaded_file(file, file_name, domain, nginx_format)
                return JsonResponse({'message': '文件上传成功'}, status=200)
            self.handle_uploaded_file(file, file_name, domain, nginx_format)
            return JsonResponse({'message': '文件上传成功'}, status=200)
        except Exception as e:
            # 表单验证  失败的情况
            return JsonResponse({'errors': e}, status=400)

    def generate_nginx_regex(self, nginx_format):
        try:
            # 预处理nginx_format字符串以移除换行符和多余的空格
            nginx_format = nginx_format.replace('\n', ' ').replace('\r', '').replace('\t', ' ').replace("'", '')
            nginx_format = re.sub(r'\s+', ' ', nginx_format).strip()

            patterns = {
                r'\$remote_addr': r'(?P<remote_addr>\\S+)',
                r'\$remote_user': r'(?P<remote_user>\\S*)',
                r'\$request_time': r'(?P<request_time>\\S+)',
                r'\[\$time_local\]': r"(?P<time_local>.*?)",
                r'\$request_method': r'(?P<request_method>\\S+)',
                r'\$scheme://\$host\$request_uri': r'(?P<request_uri>\\S+)',
                r'\$request': r'(?P<request>.+?)',
                r'\$server_protocol': r'(?P<server_protocol>.*?)',  # 修改这里的变量名，移除$
                r'\$status': r'(?P<status>\\d{3})',
                r'\$body_bytes_sent': r'(?P<body_bytes_sent>\\d+)',
                r'\$http_referer': r'(?P<http_referer>.*?)',
                r'\$http_user_agent': r'(?P<http_user_agent>.+?)',
                r'\$http_x_forwarded_for': r'(?P<http_x_forwarded_for>.*?)',
                r'\$upstream_response_time': r'(?P<upstream_response_time>\\S+)',
            }

            for variable, pattern in patterns.items():
                nginx_format = re.sub(variable, pattern, nginx_format)

            return nginx_format
        except Exception as e:
            logging.error(f'Failed to generate nginx regex: {e}')
            return None

    def handle_uploaded_file(self, file, file_name=None, domain=None, nginx_format=None):
        # 处理上传的nginx日志文件
        if file_name and file_name.endswith('.gz'):
            # 使用TemporaryFile或者BytesIO临时保存上传的文件
            with tempfile.TemporaryFile() as tmp:
                # 将上传的文件内容写入临时文件
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp.seek(0)  # 重置文件指针到开始

                # 使用gzip打开临时文件
                with gzip.open(tmp, 'rt', encoding='utf-8') as gz_file:
                    # 确保在这里重新定位到文件开始，如果你要在process_log_file中再次读取
                    self.process_log_file(gz_file, domain, nginx_format)
        else:
            # 如果文件不是压缩文件，则直接处理
            self.process_log_file(file, domain, nginx_format)

    def process_log_file(self, file, domain, nginx_format):
        # 处理日志文件
        if domain.strip() == '':  # 如果domain为空，就从文件中的request获取
            for line in file:
                if line.strip():
                    if isinstance(line, bytes):
                        line = line.decode('utf-8')
                    self.parse_nginx_log(line, website=None, nginx_format=nginx_format)
            return None

        # 获取站点信息，如果站点不存在则创建
        website, _ = WebsiteModel.objects.get_or_create(domain=domain)
        for line in file:
            # print(f'line: {line}')
            if line.strip():
                if isinstance(line, bytes):
                    line = line.decode('utf-8')
                self.parse_nginx_log(line, website, nginx_format)

    def parse_nginx_log(self, line, website, nginx_format):

        try:
            # 使用pygrok解析日志
            pattern_string = self.generate_nginx_regex(nginx_format)
            # print(f'pattern_string: {pattern_string}')
            # print(f'line: {line}')
            # 移除所有单引号
            pattern_string = pattern_string.replace("'", "")

            # 使用正则表达式将多个空格替换为一个空格
            pattern_string = re.sub(r'\s+', ' ', pattern_string).strip()

            # 使用pygrok解析日志
            grok = pygrok.Grok(pattern_string)
            match = grok.match(line)
            if match:
                log = match
                # domain = log['request'].split('/')[2]
                visit_time = log.get('time_local')
                # 移除方括号
                time_data = visit_time.strip('[]')
                # 转换成YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]日期格式
                visit_time = datetime.strptime(time_data, '%d/%b/%Y:%H:%M:%S %z')
                if website:
                    # print(f'visit_time: {visit_time}')
                    logging.info(f'Parsed log line: {log}')
                    return VisitModel.objects.get_or_create(
                        site=website,
                        visit_time=visit_time,
                        remote_addr=log.get('remote_addr'),
                        user_agent=log.get('http_user_agent', ''),
                        defaults={
                            # 'user_agent': log.get('http_user_agent', ''),
                            'path': log.get('request_uri'),
                            'method': log.get('request_method'),
                            'status_code': log.get('status'),
                            'data_transfer': log.get('body_bytes_sent'),
                            'http_referer': log.get('http_referer'),
                            'malicious_request': False,
                            'request_time': log.get('request_time')
                        }
                    )
                else:
                    domain = log.get('request_uri').split('/')[2]
                    website, _ = WebsiteModel.objects.get_or_create(domain=domain)
                    logging.info(f'Parsed log line: {log}')
                    return VisitModel.objects.get_or_create(
                        site=website,
                        visit_time=visit_time,
                        remote_addr=log.get('remote_addr'),
                        user_agent=log.get('http_user_agent', ''),
                        defaults={
                            # 'user_agent': log.get('http_user_agent', ''),
                            'path': log.get('request_uri'),
                            'method': log.get('request_method'),
                            'status_code': log.get('status'),
                            'data_transfer': log.get('body_bytes_sent'),
                            'http_referer': log.get('http_referer'),
                            'malicious_request': False,
                            'http_x_forwarded_for': log.get('http_x_forwarded_for'),
                            'request_time': log.get('request_time')
                        }
                    )
        except Exception as e:
            logging.error(f'Failed to parse log line: {e}')
            return None


def website_stats(request):
    website = request.GET.get('website')
    if website:
        try:
            data = WebsiteModel.objects.get(domain=website)
            data_dict = {
                'ip_total': data.ip_total,
                'visit_total': data.visit_total,
                'data_transfer_total': data.data_transfer_total,
                'visitor_total': data.visitor_total,
            }
            return render(request, 'website_stats.html', {'data': data_dict})
        except ObjectDoesNotExist:
            return JsonResponse({'message': '站点不存在'}, status=400)
    else:
        return render(request, 'website_stats.html')


# class WebsiteListView(ListView):
class WebsiteListAPIView(APIView):
    """
    获取站点列表
    """
    model = WebsiteModel
    template_name = 'website_list.html'
    context_object_name = 'websites'

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
        queryset = WebsiteModel.objects.all()
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
        queryset = WebsiteModel.objects.filter(id=website_id) if website_id else WebsiteModel.objects.all()
        queryset = self.filter_queryset_by_dates(queryset, dates_range)
        # 对 visitmodel__http_x_forwarded_for 进行去重计数以获得 IP 总数
        ip_totals = queryset.annotate(distinct_ip=Count('visitmodel__http_x_forwarded_for', distinct=True))

        # 对整个查询集进行计数以获得访问总数
        visit_totals = queryset.annotate(total_visits=Count('visitmodel'))

        # 对 visitmodel__http_x_forwarded_for 和 visitmodel__user_agent 的组合进行去重以获得唯一访客数
        visitor_totals = queryset.values('visitmodel__http_x_forwarded_for',
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
    queryset = WebsiteModel.objects.all()
    serializer_class = MonitorSerializer

    def get_serializer_context(self):
        context = super(WebsiteDetailAPIView, self).get_serializer_context()
        context.update({'need_nested': True})  # 设置 need_nested
        return context


class ChartDataAPIView(APIView):
    """
    获取图表数据
    """

    def get(self, request, *args, **kwargs):
        website_id = request.GET.get('id', '')
        end_date = datetime.now()
        start_date = end_date - timedelta(days=6)  # 包括今天在内的过去7天

        # 确保website_id对应的WebsiteModel存在
        if website_id and not WebsiteModel.objects.filter(id=website_id).exists():
            return Response({'error': 'Website not found'}, status=404)

        # 构建基础查询集
        queryset = VisitModel.objects.filter(visit_time__range=(start_date, end_date))
        if website_id:
            queryset = queryset.filter(site__id=website_id)

        # 按天分组，同时统计访问量和独立IP数量
        stats_per_day = queryset.annotate(day=TruncDay('visit_time')) \
            .values('day') \
            .annotate(visit_total=Count('id'), ip_total=Count('http_x_forwarded_for', distinct=True)) \
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
    @staticmethod
    def get_object(pk):
        try:
            website = WebsiteModel.objects.get(pk=pk)
            return website
        except WebsiteModel.DoesNotExist:
            return

    def to_serializer(self, ip_aggregation):
        ips_data = [{'key': bucket.key, 'doc_count': bucket.doc_count} for bucket in ip_aggregation]
        return ips_data

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response(data={"msg": "没有此域名信息"}, status=status.HTTP_404_NOT_FOUND)

        # 调用es聚合查询所有ip的数量
        aggre = Aggregation(index='visit', domain=obj.domain)
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
