from django.urls import path
from . import views

urlpatterns = [
    path('model_list/', views.model_list, name='model_list'),
]