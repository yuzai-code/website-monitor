# 查询ip所属的地理位置
import geoip2.database


def lookup_ip(ip_address, path):
    """
    查询ip所属的地理位置
    :param ip: ip地址
    :return: 地理位置
    """
    if not hasattr('ip_cache', '__dict__'):
       ip_cache={}
    if ip_address not in ip_cache:
        try:
            with geoip2.database.Reader(path) as reader:
                response = reader.country(ip_address)
                country = response.country.name
                ip_cache[ip_address] = country
        except geoip2.errors.AddressNotFoundError:
            ip_cache[ip_address] = '未知'
    return ip_cache[ip_address]