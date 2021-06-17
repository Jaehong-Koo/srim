from django.urls import path, include
from . import views

app_name='stock'

urlpatterns = [
    path('', views.intro_page),
    path('login/', views.login_page),
    path('search/<str:q>/', views.StockSearch.as_view()),
    path('about_page/', views.About_PageList.as_view()),
    path('about_srim/', views.About_SrimList.as_view()),
    path('srim/', views.StockList.as_view()),
    path('srim/<int:pk>/', views.StockDetail.as_view(), name='detail'),
    path('srim/<int:pk>/', views.StockChartView.as_view()),
    path('<int:pk>/like/', views.like, name='like'),
    path('like_list/', views.StockLikeList.as_view(), name='like_list'),
]