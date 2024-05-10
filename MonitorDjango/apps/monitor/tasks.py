import gzip
import hashlib
import os

import sys

from django.contrib.auth.models import User
from django.core.wsgi import get_wsgi_application
from django.db import transaction
from django.db.models import Count
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections, Search, Index
from rest_framework.response import Response

from monitor.es import TotalAggregation, WebsiteES, IpAggregation
from utils.dns_parse import is_googlebot, lookup_ip

sys.path.extend(['/home/yuzai/Desktop/WebsiteMonitor'])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebsiteMonitor.settings")
application = get_wsgi_application()
import logging
import re

from celery import shared_task, chord, group
from monitor.models import WebsiteModel, VisitModel, LogFileModel, TotalModel, TotalDayModel, IPDayModel
import pygrok
from datetime import datetime, timedelta
from WebsiteMonitor.settings import config

# 建立Elasticsearch连接
# connections.create_connection(hosts=['localhost:9200'], timeout=20)
elasticsearch_client = connections.create_connection(hosts=[config['es']['ES_URL']], timeout=20)


@shared_task(name='is_googlebot', queue='handle_ip')
def nslookup(user_id, date=None):
    """
    查询IP是否是googlebot，并批量更新状态
    """
    if date is None:
        date = datetime.now().date().isoformat()

    logging.info('开始执行nslookup')
    ip_list = list(IPDayModel.objects.filter(user_id=user_id, visit_date=date).values_list('ip', flat=True))
    batch_size = 100  # 根据需求调整批量大小
    ip_batches = [ip_list[i:i + batch_size] for i in range(0, len(ip_list), batch_size)]

    for ip_batch in ip_batches:
        nslookup_batch.delay(user_id, date, ip_batch)


from django.db.models import F


@shared_task(name='nslookup_batch', queue='handle_ip')
def nslookup_batch(user_id, date, ip_batch):
    """
    处理一批IP的查询和更新
    """
    logging.info('开始执行nslookup子任务')
    # 从数据库获取所有相关IP的记录
    ip_records = IPDayModel.objects.filter(user_id=user_id, visit_date=date, ip__in=ip_batch)

    # 创建一个字典，以便通过IP快速访问每个记录
    ip_record_map = {rec.ip: rec for rec in ip_records}

    # 检查每个IP是否是googlebot，并设置状态
    for ip in ip_batch:
        if ip in ip_record_map:
            record = ip_record_map[ip]
            is_bot = is_googlebot(ip)
            record.status = 1 if is_bot else 0  # 设置状态为1如果是googlebot，否则为0

    # 使用bulk_update批量更新记录，只更新'status'字段
    if ip_record_map:
        IPDayModel.objects.bulk_update(ip_record_map.values(), ['status'])

    logging.info(f'批量更新成功，处理了 {len(ip_record_map)} 个IP')


@shared_task(name='ip_day', queue='handle_ip')
def ip_day(user_id, date=None):
    if date is None:
        date = datetime.now().date().isoformat()

    # 初始化一个 IpAggregation 实例来处理IP聚合
    ip_aggr = IpAggregation(index='visit_new', user_id=user_id)
    # 获取当天IP数据以及分页查询的游标
    data, after_key = ip_aggr.get_ip_day(date=date)

    # 设置批处理大小
    batch_size = 3000  # 或根据实际情况进行调整
    ip_data_batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]

    all_tasks = [process_ip_data_batch.s(user_id, date, batch) for batch in ip_data_batches]

    # 如果存在分页数据，继续获取并添加批量任务
    while after_key:
        data, after_key = ip_aggr.get_ip_day(date=date, after_key=after_key)
        more_batches = [data[i:i + batch_size] for i in range(0, len(data), batch_size)]
        all_tasks.extend(process_ip_data_batch.s(user_id, date, batch) for batch in more_batches)

    # 创建任务组
    task_group = group(all_tasks) if all_tasks else None
    if task_group is None:
        logging.error("No tasks have been scheduled. Check the data retrieval step.")
        return

    # 定义回调任务并执行
    callback_task = nslookup.si(user_id, date)
    result = chord(task_group)(callback_task)
    return result


@shared_task(name='process_ip_data_batch', queue='handle_ip')
def process_ip_data_batch(user_id, date, ip_data_list):
    logging.info('开始执行批量IP数据处理任务')

    # 查询数据库中已存在的IP记录
    existing_ips = IPDayModel.objects.filter(
        user_id=user_id,
        visit_date=date,
        ip__in=[item['remote_addr'] for item in ip_data_list]
    ).annotate(
        total_count=Count('ip')
    ).values_list('ip', flat=True)

    existing_ip_set = set(existing_ips)

    # 准备批量创建和更新的数据列表
    to_create = []
    to_update = []

    for item in ip_data_list:
        country = lookup_ip(item['remote_addr'])
        if item['remote_addr'] in existing_ip_set:
            # 准备更新数据
            to_update.append(IPDayModel(
                user_id=user_id,
                domain=item['domain'],
                visit_date=date,
                ip=item['remote_addr'],
                count=item['count'],
                status=0,  # 或其他逻辑定义的状态
                country=country
            ))
        else:
            # 准备新建数据
            to_create.append(IPDayModel(
                user_id=user_id,
                domain=item['domain'],
                visit_date=date,
                ip=item['remote_addr'],
                count=item['count'],
                status=0,
                country=country
            ))

    # 批量创建新记录
    IPDayModel.objects.bulk_create(to_create)
    logging.info(f'成功创建{len(to_create)}条IP数据')

    # 批量更新现有记录
    # 注意: Django 默认不支持bulk_update，需要手动实现或使用update()循环每个对象
    for update_item in to_update:
        IPDayModel.objects.filter(user_id=user_id, visit_date=date, ip=update_item.ip).update(
            count=update_item.count,
            country=update_item.country
        )
    logging.info(f'成功更新{len(to_update)}条IP数据')

    return f"Processed {len(to_create) + len(to_update)} IP addresses"


@shared_task(name='total_day', queue='handle_file')
def total_day(user_id, date=None):
    """
每日统计
    :param user_id:
    :return:
    """
    if not date:
        date = datetime.now().date()
    try:
        website_es = WebsiteES(index='visit_new', user_id=user_id)
        website_list, after_key = website_es.get_website_list(date=date)
        for website in website_list:
            # 根据日期查询是否存在,来进行更新或者创建
            TotalDayModel.objects.update_or_create(user_id=user_id, domain=website['domain'], visit_date=date,
                                                   defaults={'google_referer': website['google_referer'],
                                                             'ips': website['ips'],
                                                             'google_bot': website['googlebot_count'],
                                                             'visits': website['visits'],
                                                             'data_transfers': website['data_transfers'],
                                                             'url_count': website['url_count']
                                                             })
        while after_key:
            website_list, after_key = website_es.get_website_list(date=date, after_key=after_key)
            # 保存到数据库
            for website in website_list:
                # 根据日期查询是否存在,来进行更新或者创建

                TotalDayModel.objects.update_or_create(user_id=user_id, domain=website['domain'], visit_date=date,
                                                       defaults={'google_referer': website['google_referer'],
                                                                 'ips': website['ips'],
                                                                 'google_bot': website['googlebot_count'],
                                                                 'visits': website['visits'],
                                                                 'data_transfers': website['data_transfers'],
                                                                 'url_count': website['url_count']
                                                                 })
            print('保存成功')
    except Exception as e:
        logging.error(f'每日统计失败: {e}')
        return e


@shared_task(name='total', queue='handle_file')
def total(results, user_id):
    """
    汇总,文件处理完成后调用
    :return:
    """

    # 调用es进行汇总
    total_agg = TotalAggregation(index='visit_new', user_id=user_id)
    # 聚合来自google的访问量
    google_visit = total_agg.google_visit()
    google_visit_lst = [bucket.doc_count for bucket in google_visit]
    # 聚合所有不同的ip
    es_ips = total_agg.total_ip()
    ip_date_lst = [bucket.key_as_string for bucket in es_ips]
    # 将时间字符串转换为日期
    ip_date = [datetime.strptime(date, '%Y-%m-%dT%H:%M:%S.%fZ').date() for date in ip_date_lst]
    ip_count_lst = [bucket.unique_ips.value for bucket in es_ips]
    # 聚合来自goole的爬虫
    es_googlebot = total_agg.google_bot()
    googlebot_lst = [bucket.doc_count for bucket in es_googlebot]
    # 聚合统计所有的访问量
    es_total_visit = total_agg.total_visit()
    total_visit_lst = [bucket.doc_count for bucket in es_total_visit]

    user_instance = User.objects.get(id=user_id)
    # 保存到数据库
    for i in range(len(google_visit_lst)):
        # 根据日期查询是否存在,来进行更新或者创建
        TotalModel.objects.update_or_create(user=user_instance, visit_date=ip_date[i],
                                            defaults={'google_visit': google_visit_lst[i],
                                                      'total_ip': ip_count_lst[i],
                                                      'google_bot': googlebot_lst[i],
                                                      'total_visit': total_visit_lst[i],
                                                      })


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
    callback = total.s(user_id=user_id) | total_day.si(user_id=user_id) | ip_day.si(user_id=user_id) | nslookup.si(
        user_id=user_id)
    result = chord(tasks)(callback)


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
