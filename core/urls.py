# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('progress/', views.progress_view, name='progress'), 
    
    path('api/status/', views.api_status, name='api_status'),
]