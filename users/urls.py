# users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('update/', views.UserUpdateView.as_view(), name='update'),
    path('preferences/', views.user_preferences, name='preferences'),
    path('complete-setup/', views.complete_profile_setup, name='complete-setup'),
    path('nutrition-goals/', views.nutrition_goals, name='nutrition-goals'),
]