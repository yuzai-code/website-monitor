import gzip
import hashlib
import os

import sys

from django.contrib.auth.models import User
from django.core.wsgi import get_wsgi_application
from django.db import transaction
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections, Search, Index
from rest_framework.response import Response

from monitor.es import TotalAggregation

sys.path.extend(['/home/yuzai/Desktop/WebsiteMonitor'])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebsiteMonitor.settings")
application = get_wsgi_application()
import logging
import re

from celery import shared_task, chord
from monitor.models import WebsiteModel, VisitModel, LogFileModel,  TotalModel
import pygrok
from datetime import datetime, timedelta
from WebsiteMonitor.settings import config

# 建立Elasticsearch连接
# connections.create_connection(hosts=['localhost:9200'], timeout=20)
elasticsearch_client = connections.create_connection(hosts=[config['es']['ES_URL']], timeout=20)


@shared_task(name='total', queue='handle_file')
def total(results, user_id):
    """
    汇总,文件处理完成后调用
    :return:
    """

    # 调用es进行汇总
    total_agg = TotalAggregation(index='visit_new', user_id=user_id)
    total_visit = total_agg.google_visit()
    visit_count = [bucket.doc_count for bucket in total_visit]
    es_ips = total_agg.total_ip()
    ip_date = [bucket.key_as_string for bucket in es_ips]
    # 将时间字符串转换为日期
    ip_date = [datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').date() for date in ip_date]
    ip_count = [bucket.unique_ips.value for bucket in es_ips]
    es_google_ips = total_agg.google_bot()
    google_ips_counts = [bucket.doc_count for bucket in es_google_ips]
    # logging.info(f'user_id: {user_id}, visit_count: {visit_count}, ip_date: {ip_date}, ip_count: {ip_count}, '
    #              f'google_ips_counts: {google_ips_counts}')

    user_instance = User.objects.get(id=user_id)
    # 保存到数据库
    for i in range(len(visit_count)):
        # print(ip_date[i], visit_count[i], ip_count[i], google_ips_counts[i])
        # 根据日期查询是否存在,来进行更新或者创建
        TotalModel.objects.update_or_create(user=user_instance, visit_date=ip_date[i],
                                            defaults={'google_visit': visit_count[i], 'total_ip': ip_count[i],
                                                      'google_bot': google_ips_counts[i]})


@shared_task(name='handle_file', queue='handle_file')
def handle_uploaded_file_task(nginx_format, file_path, user_id, domain):
    BATCH_SIZE = 1000
    pattern_string = generate_nginx_regex(nginx_format)
    pattern_string = pattern_string.replace("'", "")
    pattern_string = re.sub(r'\s+', ' ', pattern_string).strip()

    tasks = []
    if file_path.endswith('.gz'):
        open_func = gzip.open
    else:
        open_func = open

    with open_func(file_path, 'rt', encoding='utf-8') as file:
        batch_lines = []
        for line in file:
            batch_lines.append(line)
            if len(batch_lines) >= BATCH_SIZE:
                # 将任务添加到列表而不是直接发起
                tasks.append(process_log_batch.s(batch_lines, domain, pattern_string, user_id))
                batch_lines = []

        if batch_lines:  # 处理最后一个批次
            tasks.append(process_log_batch.s(batch_lines, domain, pattern_string, user_id))

    # 使用chord来确保所有process_log_batch任务完成后调用total任务
    result = chord(tasks)(total.s(user_id=user_id))


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
            search = Search(index='visit_new').query("match", _id=doc_id)
            response = search.execute()
            if not response.hits:
                # 如果文档不存在，则创建并保存新文档
                # 创建文档而不是立即保存
                visit_document = {
                    "_op_type": "index",
                    "_index": "visit_new",
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
