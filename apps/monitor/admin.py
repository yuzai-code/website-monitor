from django.contrib import admin

from monitor.models import WebsiteModel, VisitModel


# Register your models here.
@admin.register(WebsiteModel)
class WebsiteModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'site_name', 'site_type', 'domain', 'deploy_status', ]
    list_per_page = 50
    list_editable = ['deploy_status']
    list_filter = ['site_name', 'site_type', 'deploy_status']
    search_fields = ['site_name', 'domain']


@admin.register(VisitModel)
class VisitModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'site', 'visit_time', 'remote_addr', 'user_agent', 'path', 'method', 'status_code',
                    'data_transfer', 'http_referer', 'malicious_request', 'http_x_forwarded_for', 'request_time']
    list_per_page = 50
    list_filter = ['site', 'visit_time', 'remote_addr', 'method', 'status_code', 'malicious_request']
    search_fields = ['remote_addr', 'path', 'method', 'status_code']
