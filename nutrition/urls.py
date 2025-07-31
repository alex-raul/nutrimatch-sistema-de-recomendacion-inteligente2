# nutrition/urls.py
from django.urls import path
from . import views

app_name = 'nutrition'

urlpatterns = [
    path('categories/', views.FoodCategoryListView.as_view(), name='category-list'),
    path('foods/', views.FoodListView.as_view(), name='food-list'),
    path('foods/<int:pk>/', views.FoodDetailView.as_view(), name='food-detail'),
    path('search/', views.FoodSearchView.as_view(), name='food-search'),
    path('suggestions/', views.food_suggestions, name='food-suggestions'),
    path('analysis/', views.nutrition_analysis, name='nutrition-analysis'),
    path('similar/<int:food_id>/', views.similar_foods, name='similar-foods'),

    path('usda-search/', views.search_usda_foods, name='usda-search'),
    path('import-usda/', views.import_usda_food, name='import-usda'),
    path('enhanced-search/', views.enhanced_food_search, name='enhanced-search'),
]