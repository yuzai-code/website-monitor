import logging
import re
import gzip
import tempfile
from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import CreateView, DetailView, ListView
from pygrok import pygrok

from .forms import LogFileForm
from .models import VisitModel, WebsiteModel, LogFileModel

pattern_string = r'(?P<remote_addr>\d+\.\d+\.\d+\.\d+) - - \[(?P<time_local>.+?)\] "(?P<method>\S+) (?P<path>\S+) (?P<protocol>HTTP\/\d\.\d)" (?P<status>\d{3}) (?P<body_bytes_sent>\d+) "(?P<http_referer>[^"]*)" "(?P<user_agent>[^"]+)"'


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
        if request.is_ajax():
            form = self.form_class(request.POST, request.FILES, request)
            if form.is_valid():
                file = self.request.FILES['upload_file']
                domain = form.cleaned_data['website']
                nginx_format = self.request.POST.get('nginx_log_format')
                print(f'file: {file}')
                file_name = file.name
                self.object = form.save()
                self.handle_uploaded_file(file, file_name, domain, nginx_format)
                return JsonResponse({'message': '文件上传成功'}, status=200)
            else:
                # print(form.errors)
                # 表单验证失败的情况
                return JsonResponse({'errors': form.errors}, status=400)
        else:
            # 非Ajax请求的处理
            return super().post(request, *args, **kwargs)

    def generate_nginx_regex(self, nginx_format):
        # 生成nginx日志格式的正则表达式
        # 生成正则表达式
        try:
            patterns = {
                '$remote_addr': r'(?P<remote_addr>\S+)',
                '$remote_user': r'(?P<remote_user>\S*)',
                '$time_local': r'(?P<time_local>\[.*?\])',
                '$request': r'(?P<request>".+?")',
                '$status': r'(?P<status>\d{3})',
                '$body_bytes_sent': r'(?P<body_bytes_sent>\d+)',
                '$http_referer': r'(?P<http_referer>".*?")',
                '$http_user_agent': r'(?P<http_user_agent>".+?")',
                '$http_x_forwarded_for': r'(?P<http_x_forwarded_for>".*?")',
                '$request_time': r'(?P<request_time>\S+)',
            }

            # 转义正则表达式特殊字符
            regex_safe_log_format = re.escape(nginx_format)

            # 将日志格式中的变量替换为相应的正则表达式
            for variable, pattern in patterns.items():
                regex_safe_log_format = regex_safe_log_format.replace(re.escape(variable), pattern)

            # 返回生成的正则表达式
            return regex_safe_log_format
        except Exception as e:
            logging.error(f'Failed to generate nginx log regex: {str(e)}')
            return JsonResponse({'message': 'nginx日志配置格式输入有无，无法解析'}, status=400)

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
        print(f'Processing log file,{file}')
        # 处理日志文件
        # batch_size = 1000  # 每批处理1000行日志
        # 获取站点信息，如果站点不存在则创建
        website, _ = WebsiteModel.objects.get_or_create(domain=domain)
        for line in file:
            print(f'line: {line}')
            if line.strip():
                self.parse_nginx_log(line, website, nginx_format)

    def parse_nginx_log(self, line, website, nginx_format):
        # 解析nginx日志
        if not isinstance(line, str):
            logging.error(f"Failed to parse log line: {line} is not a string")
            return None
            # 使用pygrok解析日志
        pattern_string = self.generate_nginx_regex(nginx_format)
        grok = pygrok.Grok(pattern_string)
        match = grok.match(line)
        if match:
            log = match
            # domain = log['request'].split('/')[2]
            visit_time = log.get('time_local')
            # 转换成django日期格式
            visit_time = datetime.strptime(visit_time, '%d/%b/%Y:%H:%M:%S %z')

            VisitModel.objects.get_or_create(
                site=website,
                visit_time=visit_time,
                remote_addr=log.get('remote_addr'),
                defaults={
                    'path': log.get('path'),
                    'method': log.get('method'),
                    'status_code': log.get('status'),
                    'data_transfer': log.get('body_bytes_sent'),
                    'http_referer': log.get('http_referer'),
                    'malicious_request': False,
                    'http_x_forwarded_for': log.get('http_x_forwarded_for'),
                    'request_time': log.get('request_time')
                }
            )
            print(f'log: {log}')


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
