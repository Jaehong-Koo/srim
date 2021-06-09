from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.StockList.as_view()),
    path('<int:pk>/', views.StockDetail.as_view()),
    path('<int:pk>/', views.StockChartView.as_view()),
]