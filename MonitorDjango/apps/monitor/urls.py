"""WebsiteMonitor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.index, name='index'),
    path('nginx_logs/', views.nginx_logs, name='nginx_logs'),
    path('website_stats/', views.website_stats, name='website_stats'),

    path('upload/', views.LogUpload.as_view(), name='log_upload'),

    path('website_list/', views.WebsiteListAPIView.as_view(), name='website_list'),

    path('api/csrf_token/', views.csrf_token, name='csrf_token'),
    path('api/upload/', views.LogUpload.as_view(), name='log_upload'),
    path('api/website_list/', views.WebsiteListAPIView.as_view(), name='website_list_api'),
    path('api/chart_data/', views.ChartDataAPIView.as_view(), name='chart_data_api'),
    path('api/website_detail/<int:pk>/', views.WebsiteDetailAPIView.as_view(), name='website_detail'),
    path('api/ip_list/<int:pk>/', views.IpListAPIView.as_view(), name='ip_list')
]
