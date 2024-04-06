from django.contrib import admin

from monitor.models import WebsiteModel, VisitModel


# Register your models here.
@admin.register(WebsiteModel)
class WebsiteModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'site_name', 'site_type', 'domain', 'deploy_status', 'ip_total', 'visit_total',
                    'data_transfer_total', 'visitor_total', 'error_total', 'malicious_request_total',
                    'request_per_second', 'user']
    list_per_page = 50
    # list_editable = [ 'deploy_status']
    list_filter = ['domain', ]
    search_fields = ['domain']


@admin.register(VisitModel)
class VisitModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'site', 'visit_time', 'remote_addr', 'user_agent', 'path', 'method', 'status_code',
                    'data_transfer', 'http_referer', 'malicious_request', 'http_x_forwarded_for', 'request_time',
                    'user']
    list_per_page = 50
    list_filter = ['site', 'visit_time', 'user', 'http_referer', 'http_x_forwarded_for', 'method', 'status_code',
                   'malicious_request']
    search_fields = ['http_referer','user_agent']
