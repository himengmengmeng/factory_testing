from django.urls import path
from . import views


urlpatterns = [
    path('model_list/', views.model_list, name='model_list'),
    path('seller_login/', views.login_view, name='login'),
    path('variants/', views.variant_list, name='variant_list'),
    path('', views.login_view, name='root'),  # 根路径重定向到登录
]