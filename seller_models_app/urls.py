from django.urls import path
from . import views


urlpatterns = [
    #path('model_list/', views.model_list, name='model_list'),
    path('seller_login/', views.login_view, name='login'),
    path('variants/', views.variant_list, name='variant_list'),
    path('', views.login_view, name='root'),  # 根路径重定向到登录
    path('device-check-tool/', views.device_check_tool, name='device_check_tool'),
    path('check-devices/', views.check_and_bind_devices, name='check_devices'),
    path('get-progress/', views.get_progress, name='get_progress'),
    path('export-results/', views.export_results, name='export_results'),
    path('retry-failed/', views.retry_failed_devices, name='retry_failed'),
]


