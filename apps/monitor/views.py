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
        # print('111')
        form = self.form_class(request.POST, request.FILES, request)
        if form.is_valid():
            file = self.request.FILES['upload_file']
            domain = form.cleaned_data['website']
            nginx_format = self.request.POST.get('nginx_log_format')
            # print(f'file: {file}')
            file_name = file.name
            self.object = form.save()
            self.handle_uploaded_file(file, file_name, domain, nginx_format)
            return JsonResponse({'message': '文件上传成功'}, status=200)
        else:
            # print(form.errors)
            # 表单验证  失败的情况
            return JsonResponse({'errors': form.errors}, status=400)

    def generate_nginx_regex(self, nginx_format):
        try:
            # Preprocess the nginx_format string to remove newlines and extra spaces
            nginx_format = nginx_format.replace('\n', ' ').replace('\r', '').replace('\t', ' ').replace("'", '')
            nginx_format = re.sub(r'\s+', ' ', nginx_format).strip()

            patterns = {
                r'\$remote_addr': r'(?P<remote_addr>\\S+)',
                r'\$remote_user': r'(?P<remote_user>\\S*)',
                r'\$request_time': r'(?P<request_time>\\S+)',  # 确保这里是正确的变量名
                r'\[\$time_local\]': r"(?P<time_local>.*?)",
                r'\$request': r'(?P<request>.+?)',
                r'\$status': r'(?P<status>\\d{3})',
                r'\$body_bytes_sent': r'(?P<body_bytes_sent>\\d+)',
                r'\$http_referer': r'(?P<http_referer>.*?)',
                r'\$http_user_agent': r'(?P<http_user_agent>.+?)',
                r'\$http_x_forwarded_for': r'(?P<http_x_forwarded_for>.*?)',
                r'\$upstream_response_time': r'(?P<upstream_response_time>\\S+)',  # 添加对 upstream_response_time 的处理
            }

            for variable, pattern in patterns.items():
                nginx_format = re.sub(variable, pattern, nginx_format)

            return nginx_format
        except Exception as e:
            logging.error(f'Failed to generate nginx regex: {e}')
            return nginx_format

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
        # print(f'Processing log file,{file}')
        # 处理日志文件
        # batch_size = 1000  # 每批处理1000行日志
        # 获取站点信息，如果站点不存在则创建
        website, _ = WebsiteModel.objects.get_or_create(domain=domain)
        for line in file:
            # print(f'line: {line}')
            if line.strip():
                if isinstance(line, bytes):
                    line = line.decode('utf-8')
                self.parse_nginx_log(line, website, nginx_format)

    def parse_nginx_log(self, line, website, nginx_format):
        # 解析nginx日志
        # if not isinstance(line, str):
        #     logging.error(f"Failed to parse log line: {line} is not a string")
        #     return None
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
                # print(f'visit_time: {visit_time}')
                VisitModel.objects.get_or_create(
                    site=website,
                    visit_time=visit_time,
                    remote_addr=log.get('remote_addr'),
                    user_agent=log.get('http_user_agent', ''),
                    defaults={
                        # 'user_agent': log.get('http_user_agent', ''),
                        'path': log.get('request').split()[1],
                        'method': log.get('request').split()[0],
                        'status_code': log.get('status'),
                        'data_transfer': log.get('body_bytes_sent'),
                        'http_referer': log.get('http_referer'),
                        'malicious_request': False,
                        'http_x_forwarded_for': log.get('http_x_forwarded_for'),
                        'request_time': log.get('request_time')
                    }
                )
                logging.info(f'Parsed log line: {log}')
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
