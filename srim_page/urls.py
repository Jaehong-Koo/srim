from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.intro_page),
    path('category/<str:slug>/', views.category_page),
    path('srim/', views.StockList.as_view()),
    path('srim/<int:pk>/', views.StockDetail.as_view()),
    path('srim/<int:pk>/', views.StockChartView.as_view()),
]