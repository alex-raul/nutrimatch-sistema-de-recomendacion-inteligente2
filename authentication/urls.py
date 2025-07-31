# authentication/urls.py
from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    # Vistas HTML
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile-setup/', views.profile_setup_view, name='profile_setup'),
    
    # APIs
    path('api/register/', views.api_register, name='api_register'),
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/profile/', views.api_profile, name='api_profile'),
    path('api/change-password/', views.api_change_password, name='api_change_password'),
]