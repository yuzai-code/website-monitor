import os

import sys

from django.core.wsgi import get_wsgi_application

sys.path.extend(['/home/yuzai/Desktop/WebsiteMonitor'])
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebsiteMonitor.settings")
application = get_wsgi_application()
import configparser
import logging
import re
import select
import paramiko
from celery import shared_task
from monitor.models import WebsiteModel, VisitModel
import pygrok
from django.db.models import Count
from datetime import datetime, timedelta

# 全局变量存储配置信息
config = configparser.ConfigParser()
config.read('config.ini')

# SSH连接池
ssh_pool = paramiko.SSHClient()
ssh_pool.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_pool.connect(hostname=config['SSH']['hostname'], port=int(config['SSH']['port']),
                 username=config['SSH']['username'], password=config['SSH']['password'])

pattern = re.compile(
    r'(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<time_local>.+?)\] "(?P<request>.+?)" '
    r'(?P<status>\d{3}) (?P<body_bytes_sent>\d+) "(?P<http_referer>.+?)" "(?P<user_agent>.+?)" '
    r'"(?P<http_x_forwarded_for>.+?)" "(?P<request_time>.+?)"',
    re.DOTALL
)
pattern_string = (
    r'(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<time_local>.+?)\] "(?P<request>.+?)" '
    r'(?P<status>\d{3}) (?P<body_bytes_sent>\d+) "(?P<http_referer>.+?)" "(?P<user_agent>.+?)" '
    r'"(?P<http_x_forwarded_for>.+?)" "(?P<request_time>.+?)"'
)


def get_ssh_connection():
    """
    Establishes and returns an SSH connection using global configuration.
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(
        hostname=config['SSH']['hostname'],
        port=int(config['SSH']['port']),
        username=config['SSH']['username'],
        password=config['SSH']['password']
    )
    return ssh_client


@shared_task(name='process_nginx_logs', queue='process_nginx_logs')
def process_nginx_logs():
    """
    处理nginx日志文件
    """
    try:
        # Using the global SSH connection pool to get a connection
        ssh_client = get_ssh_connection()

        # Execute the tail -F command to get the real-time log stream
        channel = ssh_client.invoke_shell()
        channel.send(f'tail -F {config["Log"]["path"]}\n')
        channel_file = channel.makefile('r')

        logs_to_create = []
        for line in channel_file:
            if line.strip() and pattern.match(
                    line):  # Ignore empty lines and lines that don't match the Nginx log pattern
                logging.info(f"Processing line of type {type(line)}: {line}")
                log = parse_nginx_log(line)
                if log:
                    logs_to_create.append(log)

        # Batch create visit information
        if logs_to_create:
            VisitModel.objects.bulk_create(logs_to_create)

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    finally:
        ssh_client.close()


@shared_task(name='parse_nginx_log', queue='parse_nginx_log')
def parse_nginx_log(log_line):
    """
    解析nginx日志
    """
    print(log_line)
    # 检查log_line是否为字符串
    if not isinstance(log_line, str):
        logging.error(f"Failed to parse log line: {log_line} is not a string")
        return None
        # 使用pygrok解析日志

    # 使用pygrok解析日志
    grok = pygrok.Grok(pattern_string)
    match = grok.match(log_line)
    if match:
        log = match
        # 获取站点信息，如果站点不存在则创建
        domain = log['request'].split('/')[2]
        website, _ = WebsiteModel.objects.get_or_create(domain=domain)
        # 创建访问信息
        return VisitModel(
            site=website,
            visit_time=log['time_local'],
            remote_addr=log['remote_addr'],
            user_agent=log['user_agent'],
            path=log['request'].split(' ')[1].split('?')[0].strip(),
            method=log['request'].split(' ')[0].strip(),
            status_code=log['status'],
            data_transfer=log['body_bytes_sent'],
            http_referer=log['http_referer'],
            malicious_request=False,
            http_x_forwarded_for=log['http_x_forwarded_for'],
            request_time=log['request_time']
        )
    else:
        logging.error(f"Failed to parse log line: {log_line}")
        return None


@shared_task(name='check_malicious_requests', queue='check_malicious_requests')
def check_malicious_requests():
    """
    检测恶意请求
    """
    # 获取一段时间内的请求数据
    time_threshold = datetime.now() - timedelta(minutes=30)
    visits = VisitModel.objects.filter(visit_time__gte=time_threshold)

    # 检测频繁的请求
    # ip_counts = visits.values('remote_addr').annotate(count=Count('remote_addr')).order_by('-count')
    # for ip_count in ip_counts:
    #     if ip_count['count'] > 100:  # 如果一个IP在一小时内的请求次数超过100次，我们认为它可能是恶意的
    #         malicious_ips = VisitModel.objects.filter(remote_addr=ip_count['remote_addr'])
    #         malicious_ips.update(malicious_request=True)

    # 检测非法的请求
    malicious_requests = visits.filter(status_code__gte=400)
    malicious_requests.update(malicious_request=True)

    # 检测可疑的用户代理
    suspicious_user_agents = visits.filter(user_agent__contains='bot')
    suspicious_user_agents.update(malicious_request=True)


# 检测恶意请求


if __name__ == '__main__':
    process_nginx_logs()
