from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='tbft_login'),
    path('logout/', views.logout_view, name='tbft_logout'),
    path('dashboard/', views.dashboard_view, name='tbft_dashboard'),
    path('operations/', views.operations_view, name='tbft_operations'),

    # JSON API endpoints
    path('api/variants/', views.api_get_variants, name='tbft_api_variants'),
    path('api/sub-sellers/', views.api_get_sub_sellers, name='tbft_api_sub_sellers'),
    path('api/sub-sellers/<str:sub_seller_id>/variants/',
         views.api_get_sub_seller_variants, name='tbft_api_sub_seller_variants'),
    path('api/query-did/', views.api_query_did, name='tbft_api_query_did'),
    path('api/bind-did/', views.api_bind_did, name='tbft_api_bind_did'),
    path('api/batch-bind/', views.api_batch_bind, name='tbft_api_batch_bind'),
]
