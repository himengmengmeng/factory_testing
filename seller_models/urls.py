from django.urls import path
from . import views

urlpatterns = [
    path('models/', views.model_list, name='model_list'),
]