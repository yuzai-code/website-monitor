from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from utils.basemodel import BaseModel


class IPDayModel(BaseModel):
    """
    每日IP统计
    """
    STATUS = (
        (0, '其他'),
        (1, 'googlebot'),
        (2, '异常'),
    )
    domain = models.CharField(max_length=100, verbose_name='域名', blank=True, null=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='用户', null=True, blank=True)
    ip = models.CharField(max_length=100, verbose_name='IP', blank=True, null=True, db_index=True)
    country = models.CharField(max_length=100, verbose_name='国家', blank=True, null=True)
    count = models.IntegerField(verbose_name='IP数量', default=0)
    status = models.IntegerField(choices=STATUS, default=0, verbose_name='状态')
    visit_date = models.DateField(default=None, verbose_name='日期', db_index=True)

    class Meta:
        db_table = 't_ip_day'
        verbose_name = '每日IP统计'
        verbose_name_plural = verbose_name


# Create your models here.
class TotalDayModel(BaseModel):
    """
    每日统计
    """
    domain = models.CharField(max_length=100, verbose_name='域名', blank=True, null=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='用户', null=True, blank=True)
    google_referer = models.IntegerField(verbose_name='来自google的访问量', default=0)
    ips = models.IntegerField(verbose_name='总访问IP数', default=0)
    google_bot = models.IntegerField(verbose_name='GoogleBot访问量', default=0)
    visits = models.IntegerField(verbose_name="统计访问量", default=0)
    data_transfers = models.BigIntegerField(verbose_name='数据传输总量', blank=True, null=True)
    url_count = models.IntegerField(verbose_name='唯一的url总数', blank=True, null=True)
    visit_date = models.DateField(default=None, verbose_name='日期', db_index=True)

    class Meta:
        db_table = 't_total_day'
        verbose_name = '每日统计'
        verbose_name_plural = verbose_name


class TotalModel(BaseModel):
    """
    汇总
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='用户', null=True, blank=True)
    google_visit = models.IntegerField(verbose_name='来自google的总访问量', default=0)
    total_ip = models.IntegerField(verbose_name='总访问IP数', default=0)
    google_bot = models.IntegerField(verbose_name='GoogleBot访问量', default=0)
    total_visit = models.IntegerField(verbose_name="统计访问量", default=0)
    visit_date = models.DateField(default=None, verbose_name='日期', db_index=True)

    class Meta:
        db_table = 't_total'
        verbose_name = '汇总'
        verbose_name_plural = verbose_name


class UserSettingsModel(BaseModel):
    """
    用户设置
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户', related_name='user_settings')
    nginx_log_format = models.TextField(verbose_name='Nginx日志格式', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s settings"

    class Meta:
        db_table = 't_user_settings'
        verbose_name = '用户设置'
        verbose_name_plural = verbose_name


class LogFileModel(BaseModel):
    STATUS = (
        (0, 'error'),
        (1, 'processing'),
        (2, 'complete'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='用户', null=True, blank=True)
    website = models.ForeignKey('WebsiteModel', on_delete=models.CASCADE, verbose_name='站点', blank=True, null=True)
    upload_file = models.FileField(upload_to='log/', verbose_name='上传文件')
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    status = models.IntegerField(default=1, verbose_name='处理状态')
    nginx_log_format = models.CharField(max_length=600, verbose_name='Nginx日志格式', blank=True, null=True)

    class Meta:
        db_table = 't_log_file'
        verbose_name = '日志文件'
        verbose_name_plural = verbose_name

    def get_absolute_url(self):
        return reverse('index')


class WebsiteModel(BaseModel):
    """
    站点信息
    """
    DEPLOY_STATUS = (
        (0, '未部署'),
        (1, '已部署'),
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='用户1', null=True, blank=True)
    site_name = models.CharField(max_length=100, verbose_name='站点名称', blank=True, null=True)
    site_type = models.CharField(max_length=100, verbose_name='站点类型', blank=True, null=True)
    domain = models.CharField(max_length=100, verbose_name='域名', blank=True, null=True)
    deploy_status = models.IntegerField(choices=DEPLOY_STATUS, default=1, verbose_name='部署状态')
    nginx_log_format = models.CharField(max_length=255, verbose_name='Nginx日志格式', blank=True, null=True)
    ip_total = models.IntegerField(verbose_name='访问IP总数', default=0)
    visit_total = models.IntegerField(verbose_name='总访问量', default=0)
    data_transfer_total = models.BigIntegerField(verbose_name='总数据传输量', blank=True, null=True)
    visitor_total = models.IntegerField(verbose_name='总访客数', default=0)
    error_total = models.IntegerField(verbose_name='错误数', default=0)
    malicious_request_total = models.IntegerField(verbose_name='恶意请求数', default=0)
    request_per_second = models.FloatField(verbose_name='每秒请求数', blank=True, null=True)

    # date = models.DateField(auto_now_add=True, verbose_name='日期', blank=True, null=True)

    def __str__(self):
        return self.domain

    class Meta:
        db_table = 't_website'
        verbose_name = '站点信息'
        verbose_name_plural = verbose_name


class VisitModel(BaseModel):
    """
    访问信息
    """
    user = models.ForeignKey(User, on_delete=models.SET_NULL, verbose_name='用户', null=True, blank=True)
    site = models.ForeignKey(WebsiteModel, on_delete=models.CASCADE, verbose_name='站点')
    visit_time = models.DateTimeField(verbose_name='访问时间', db_index=True)
    remote_addr = models.GenericIPAddressField(verbose_name='客户端IP', blank=True, null=True, db_index=True)
    user_agent = models.CharField(max_length=255, verbose_name='User-Agent', blank=True, null=True, db_index=True)
    path = models.CharField(max_length=1000, verbose_name='访问路径', blank=True, null=True)
    method = models.CharField(max_length=100, verbose_name='请求方法', blank=True, null=True, db_index=True)
    status_code = models.IntegerField(verbose_name='HTTP状态码', db_index=True)
    HTTP_protocol = models.CharField(verbose_name="HTTP协议", max_length=20, blank=True, null=True)
    data_transfer = models.BigIntegerField(verbose_name='数据传输总量')
    http_referer = models.CharField(max_length=255, verbose_name='HTTP_REFERER', blank=True, null=True)
    malicious_request = models.BooleanField(default=False, verbose_name='是否恶意请求', db_index=True)
    http_x_forwarded_for = models.CharField(max_length=100, verbose_name='实际的客户端IP', blank=True, null=True,
                                            db_index=True)
    request_time = models.FloatField(verbose_name='请求时间', blank=True, null=True)

    class Meta:
        db_table = 't_visit'
        verbose_name = '访问信息'
        verbose_name_plural = verbose_name
        ordering = ['-visit_time']

    def __str__(self):
        return self.remote_addr


class TodayTotalModel(BaseModel):
    """
    流量信息
    """
    website = models.ForeignKey(WebsiteModel, on_delete=models.CASCADE, verbose_name='站点', default=1)
    ip_today = models.IntegerField(verbose_name='当天访问IP数', blank=True, null=True)
    traffic_time = models.DateField(verbose_name='流量日期')
    traffic_today = models.BigIntegerField(verbose_name='当天传输数据量', blank=True, null=True)
    visit_today = models.IntegerField(verbose_name='当天访问量', default=0)
    visitor_today = models.IntegerField(verbose_name='当天访客量', default=0)

    class Meta:
        db_table = 't_today_total'
        verbose_name = '流量信息'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.traffic_time} - {self.website.domain}"

# class TotalModel(BaseModel):
#     """
#     资源信息
#     """
#
#     class Meta:
#         db_table = 't_total'
#         verbose_name = '资源信息'
#         verbose_name_plural = verbose_name
#
#     def __str__(self):
#         return self.website.domain
