import socket

import geoip2.database
from gevent.resolver.dnspython import dns


def lookup_ip(ip_address):
    """
    查询IP地址
    """
    db_path = '/home/yuzai/Project/website-monitor-dev/MonitorDjango/utils/GeoLite2-Country.mmdb'  # todo 容器中注意修改路径
    if not hasattr('ip_cache', '__dict__'):
        ip_cache = {}
    if ip_address not in ip_cache:
        with geoip2.database.Reader(db_path) as reader:
            try:
                response = reader.country(ip_address)
                country = response.country.name
                ip_cache[ip_address] = country
            except geoip2.errors.AddressNotFoundError:
                ip_cache[ip_address] = '未知'
    return ip_cache[ip_address]


def is_googlebot(ip):
    try:
        # 获取反向DNS名称
        rev_name = dns.reversename.from_address(ip)
        # 设置超时并进行查询
        answers = dns.resolver.resolve(rev_name, 'PTR', lifetime=1)  # 5秒超时

        # 检查是否是Googlebot的IP
        for rdata in answers:
            print(rdata.target.to_text())
            if rdata.target.to_text().endswith("googlebot.com."):
                return True
        return False
    except dns.resolver.Timeout:
        print(f"Timeout occurred when resolving {ip}")
        return False
    except dns.resolver.NXDOMAIN:
        print("No such domain")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == "__main__":
    ip = '66.249.66.33'
    print(is_googlebot(ip))
