import gzip
import hashlib
import os

import sys

from django.core.wsgi import get_wsgi_application
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections, Search, Index
from rest_framework.response import Response

sys.path.extend(['/home/yuzai/Desktop/WebsiteMonitor'])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebsiteMonitor.settings")
application = get_wsgi_application()
import logging
import re

from celery import shared_task
from monitor.models import WebsiteModel, VisitModel, LogFileModel, UserSettingsModel
import pygrok
from datetime import datetime, timedelta
from WebsiteMonitor.settings import config

# 建立Elasticsearch连接
# connections.create_connection(hosts=['localhost:9200'], timeout=20)
elasticsearch_client = connections.create_connection(hosts=[config['es']['ES_URL']], timeout=20)


@shared_task(name='handle_file', queue='handle_file')
def handle_uploaded_file_task(log_file_id, domain):
    BATCH_SIZE = 1000  # 设置批量处理的大小
    try:
        log_file = LogFileModel.objects.get(id=log_file_id)
        file_path = log_file.upload_file.path
        nginx_format = UserSettingsModel.objects.get(user=log_file.user).nginx_log_format

        # 使用pygrok解析日志
        pattern_string = generate_nginx_regex(nginx_format)

        # 移除所有单引号
        pattern_string = pattern_string.replace("'", "")

        # 使用正则表达式将多个空格替换为一个空格
        pattern_string = re.sub(r'\s+', ' ', pattern_string).strip()
        # 检查文件是否是gzip压缩文件
        if file_path.endswith('.gz'):
            open_func = gzip.open
        else:
            open_func = open

        with open_func(file_path, 'rt', encoding='utf-8') as file:
            lines = file.readlines()
        for i in range(0, len(lines), BATCH_SIZE):
            batch_lines = lines[i:i + BATCH_SIZE]
            process_log_batch.delay(batch_lines, domain, pattern_string, log_file.user.id)
    except LogFileModel.DoesNotExist:
        logging.error(f'文件的id不存在:{log_file_id} ')


@shared_task(name='process_log_batch', queue='handle_file')
def process_log_batch(lines, domain, pattern_string, user_id):
    batch = []
    for line in lines:
        process_log_file(batch, line, domain, pattern_string, user_id)

    if batch:
        bulk_save_to_elasticsearch(batch)


def bulk_save_to_elasticsearch(documents):
    try:
        # Perform the bulk operation
        success, failed = bulk(elasticsearch_client, documents)
        if not success:
            logging.error(f'Bulk operation had issues, failed count: {failed}')
        return success
    except Exception as e:
        logging.error(f'Failed to execute bulk operation: {e}')
        return False


def process_log_file(batch, line, domain, pattern_string, user_id=None):
    # logging.info('batch: {}'.format(batch))
    # 处理日志文件
    if domain.strip() == '':  # 如果domain为空，就从文件中的request获取
        parse_nginx_log(batch, line, domain=None, pattern_string=pattern_string, user_id=user_id)
        return None

    parse_nginx_log(batch, line, domain, pattern_string, user_id=user_id)


def generate_document_id(*args):
    """
    生成基于日志内容的唯一标识符，例如使用md5
    """
    unique_string = '-'.join(str(arg) for arg in args)
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()


def parse_nginx_log(batch, line, domain, pattern_string, user_id):
    try:
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

            # 处理remote_addr
            if log.get('http_x_forwarded_for'):
                remote_addr = log.get('http_x_forwarded_for')
            else:
                remote_addr = log.get('remote_addr')

            # 判断并处理路径
            if log.get('request'):
                parts = log.get('request').split(' ', 2)
                method = parts[0]
                path = parts[1]
                HTTP_protocol = parts[2]
            else:
                method = log.get('request_method'),
                path = log.get('request_uri'),
                HTTP_protocol = log.get('server_protocol')
            if domain:
                domain = domain
            else:
                if log.get('request_uri'):
                    domain = log.get('request_uri').split('/')[2]
                else:
                    domain = log.get('request').split('/')[2]

            # 生成文档ID
            doc_id = generate_document_id(visit_time, remote_addr, path, user_id)

            # 检查文档是否存在
            search = Search(index='visit').query("match", _id=doc_id)
            response = search.execute()
            if not response.hits:
                # 如果文档不存在，则创建并保存新文档
                # 创建文档而不是立即保存
                visit_document = {
                    "_op_type": "index",
                    "_index": "visit",
                    "_id": doc_id,
                    "_source": {
                        "domain": domain,
                        "remote_addr": log.get('remote_addr'),
                        "http_x_forwarded_for": log.get('remote_addr'),
                        "user_id": user_id,
                        "path": path,
                        "visit_time": visit_time,
                        "user_agent": log.get('http_user_agent'),
                        "method": method,
                        "HTTP_protocol": HTTP_protocol,
                        "status_code": log.get('status'),
                        "data_transfer": log.get('body_bytes_sent'),
                        "http_referer": log.get('http_referer'),
                        "malicious_request": log.get('malicious_request'),
                        "request_time": log.get('request_time')
                    }
                }
                # 将文档添加到批处理队列
                batch.append(visit_document)

    except Exception as e:
        logging.error(f'解析日志文件失败: {e}, {line}')
        return e


def generate_nginx_regex(nginx_format):
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
        return Response()

# 检测恶意请求

#
# if __name__ == '__main__':
#  process_nginx_logs()
